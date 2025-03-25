import socket
import socketserver
from socketserver import BaseRequestHandler
from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE
from threading import Thread
import dns_cache_instructions as dns_cache
import ssl
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

UPSTREAM_DNS = "8.8.8.8"
UPSTREAM_PORT = 53

class DNSUDPhandler(BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        client_socket = self.request[1]
        if len(data) < 12:  # Minimum DNS header size is 12 bytes
            print("Received malformed DNS packet, ignoring.")
            return

        try:
            request = DNSRecord.parse(data)
            qname = str(request.q.qname)
            print("Requested query: ", qname)

            entry_cache = dns_cache.get_ip(qname)

            if not entry_cache:
                if request.header.tc == 1:
                    self.query_via_tcp(data, client_socket, qname)
                    return

                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as upstream_socket:
                    upstream_socket.settimeout(2)
                    upstream_socket.sendto(data, (UPSTREAM_DNS, UPSTREAM_PORT))

                    response, _ = upstream_socket.recvfrom(512)

                    client_socket.sendto(response, self.client_address)

                    upstream_dns_response = DNSRecord.parse(response)
                    dns_cache.insert(qname, upstream_dns_response)

                    print("Forwarded to upstream UDP dns")

            else:
                response = DNSRecord(
                    DNSHeader(id=request.header.id, qr=1, aa=1, ra=1),
                    q=request.q,
                    a=RR(qname, QTYPE.A, rdata=A(entry_cache["ip"]), ttl=entry_cache["ttl"])
                )

                client_socket.sendto(response.pack(), self.client_address)
                print("[UDP]Served from cache:", qname, "->", entry_cache["ip"])

        except socket.timeout:
            print("UDP server got timed out")
        except Exception as e:
            print("Error occurred at UDP: ", e)


    def query_via_tcp(self, data, client_socket, qname):
        """Retransmit the data through tcp due to error in udp truncation"""

        try:
            entry_cache = dns_cache.get_ip(qname)
            if entry_cache:
                response = DNSRecord(
                    DNSHeader(id=request.header.id, qr=1, aa=1, ra=1),
                    q=request.q,
                    a=RR(qname, QTYPE.A, rdata=A(entry_cache["ip"]), ttl=entry_cache["ttl"])
                )
                client_socket.sendall(len(response.pack()).to_bytes(2, "big") + response.pack())
                print("[HYBRID]Served from cache:", qname, "->", entry_cache["ip"])
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as upstream_tcp_socket:
                    upstream_tcp_socket.settimeout(5)
                    upstream_tcp_socket.connect((UPSTREAM_DNS, UPSTREAM_PORT))

                    upstream_tcp_socket.sendall(len(data).to_bytes(2, "big") + data)

                    response_length_bytes = upstream_tcp_socket.recv(2)
                    response_length = int.from_bytes(response_length_bytes, "big")

                    dns_response = b""
                    while len(dns_response) < response_length:
                        chunk = upstream_tcp_socket.recv(min(1024, response_length - len(dns_response)))
                        if not chunk:
                            break
                        dns_response += chunk

                    client_socket.sendto(dns_response[2:], self.client_address)

                    print("forwarded to HYBRID TCP server")

        except socket.timeout:
            print("HYBRID TCP server timeout")
        except Exception as e:
            print("Error occurred at TCP: ", e)
            return b""

class DNSTCPhandler(socketserver.BaseRequestHandler):
    def handle(self):
        client_socket = self.request

        try:
            query_length_bytes = client_socket.recv(2)
            if not query_length_bytes:
                return
            query_length = int.from_bytes(query_length_bytes, "big")

            dns_query = client_socket.recv(query_length)
            request = DNSRecord.parse(dns_query)
            qname = str(request.q.qname)

            entry_cache = dns_cache.get_ip(qname)

            if entry_cache:
                response = DNSRecord(
                    DNSHeader(id=request.header.id, qr=1, aa=1, ra=1),
                    q=request.q,
                    a=RR(qname, QTYPE.A, rdata=A(entry_cache["ip"]), ttl=entry_cache["ttl"])
                )
                client_socket.sendall(len(response.pack()).to_bytes(2, "big") + response.pack())
                print("[TCP]Served from cache:", qname, "->", entry_cache["ip"])
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as upstream_socket:
                    upstream_socket.settimeout(5)
                    upstream_socket.connect((UPSTREAM_DNS, UPSTREAM_PORT))

                    upstream_socket.sendall(len(dns_query).to_bytes(2, "big") + dns_query)

                    response_length_bytes = upstream_socket.recv(2)
                    if not response_length_bytes:
                        print("[TCP] Failed to receive length bytes.")
                        return
                    response_length = int.from_bytes(response_length_bytes, "big")

                    dns_response = b""
                    while len(dns_response) < response_length:
                        chunk = upstream_socket.recv(min(1024, response_length - len(dns_response)))
                        if not chunk:
                            break
                        dns_response += chunk

                    client_socket.sendall(response_length_bytes + dns_response)

                    print("forwarded to PURE TCP server")

        except socket.timeout:
            print("PURE TCP server timeout")
        except Exception as e:
            print("Error occurred at TCP: ", e)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="/Users/deathknight1/PycharmProjects/KnoxDNS/.venv/main/cert.pem", keyfile="/Users/deathknight1/PycharmProjects/KnoxDNS/.venv/main/privkey.pem")

UPSTREAM_DOH = "https://8.8.8.8/dns-query"

class DOHHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        dns_query = self.rfile.read(content_length)

        headers = {'Content-Type': "application/dns-,message"}
        response = requests.post(UPSTREAM_DOH, headers= headers, data = dns_query)

        if response.status_code == 200:
            self.send_response(200)
            self.send_header("Content-Type", "application/dns-message")
            self.end_headers()
            self.wfile.write(response.content)
        else:
            self.send_response(500)
            self.end_headers()

if __name__ == '__main__':
    with socketserver.UDPServer(('0.0.0.0',53) , DNSUDPhandler) as udpserver, \
        socketserver.TCPServer(('0.0.0.0',53) , DNSTCPhandler) as tcpserver:
        print("Multithreaded server now active!")
        Thread(target=udpserver.serve_forever, daemon=True).start()
        Thread(target=udpserver.serve_forever, daemon=True).start()


        httpd = HTTPServer(("0.0.0.0", 443), DOHHandler)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        print("DNS-over-HTTPS (DoH) server is running on port 443...")
        httpd.serve_forever()