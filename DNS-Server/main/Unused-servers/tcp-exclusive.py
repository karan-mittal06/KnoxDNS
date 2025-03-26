import socket
import socketserver
from dnslib import DNSRecord, DNSHeader, RR, QTYPE, A

UPSTREAM_DNS = "8.8.8.8"
UPSTREAM_PORT = 53

class DNSTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        client_socket = self.request

        try:
            query_length_bytes = client_socket.recv(2)
            query_length = int.from_bytes(query_length_bytes, "big")

            dns_query = client_socket.recv(query_length)

            upstream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            upstream_socket.connect((UPSTREAM_DNS, UPSTREAM_PORT))
            upstream_socket.sendall(len(dns_query).to_bytes(2, "big") + dns_query)

            response_socket_bytes = upstream_socket.recv(2)
            response_socket_length = int.from_bytes(response_socket_bytes, "big")

            dns_response = b""
            while len(dns_response) < response_socket_length:
                dns_response += upstream_socket.recv(response_socket_length - len(dns_response))

            client_socket.sendall(response_socket_bytes)
            client_socket.sendall(dns_response)

        except Exception as e:
            print("error occurred: ", e)

if __name__ == '__main__':
    server = socketserver.TCPServer(('0.0.0.0', 53), DNSTCPHandler)
    print("server running")
    server.serve_forever()