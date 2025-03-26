import socket
import socketserver
from socketserver import BaseRequestHandler
from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE
from threading import Thread

UPSTREAM_DNS = "8.8.8.8"
UPSTREAM_PORT = 53

class DNSUDPhandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        client_socket = self.request[1]

        try:
            request = DNSRecord.parse(data)
            qname = str(request.q.qname)
            print("Requested query: ", qname)

            if request.header.tc == 1:
                self.query_via_tcp(data, client_socket)
                return

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as upstream_socket:
                upstream_socket.settimeout(2)
                upstream_socket.sendto(data, (UPSTREAM_DNS, UPSTREAM_PORT))

                response, _ = upstream_socket.recvfrom(512)

                client_socket.sendto(response, self.client_address)

                print("Forwarded to upstream UDP dns")

        except socket.timeout:
            print("UDP server got timed out")
        except Exception as e:
            print("Error occurred at UDP: ", e)


    def query_via_tcp(self, data, client_socket):
        """Retransmit the data through tcp due to error in udp truncation"""

        try:
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

                client_socket.sendall(response_length_bytes)
                client_socket.sendall(dns_response)

                print("forwarded to PURE TCP server")

        except socket.timeout:
            print("PURE TCP server timeout")
        except Exception as e:
            print("Error occurred at TCP: ", e)


if __name__ == '__main__':
    with socketserver.UDPServer(('0.0.0.0',53) , DNSUDPhandler) as udpserver, \
        socketserver.TCPServer(('0.0.0.0',53) , DNSTCPhandler) as tcpserver:
        print("Multithreaded server now active!")

        Thread(target=udpserver.serve_forever, daemon=True).start()
        tcpserver.serve_forever()