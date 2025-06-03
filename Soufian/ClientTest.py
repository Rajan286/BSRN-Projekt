import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
message = "whois yasmin"
sock.sendto(message.encode(), ("127.0.0.1", 5000))
response, addr = sock.recvfrom(1024)
print(f"[Client] Antwort vom Server: {response.decode()}")