import socket
from peer import Peer

peers = {}
udp_port = 5011
handle = "Rajan"

def send_join():
    msg = f"JOIN {handle} {udp_port}\n"
    udp_sock.sendto(msg.encode(), ("127.0.0.1", 5010))  # an Test senden

def send_leave():
    msg = f"LEAVE {handle}\n"

    # Sende an alle bekannten Peers
    for peer in peers.values():
        udp_sock.sendto(msg.encode(), (peer.ip, peer.port))

    # Redundanz: direkt an Test
    udp_sock.sendto(msg.encode(), ("127.0.0.1", 5010))

def receive_loop():
    while True:
        data, addr = udp_sock.recvfrom(1024)
        msg = data.decode().strip()

        if msg.startswith("JOIN"):
            _, h, p = msg.split()
            peers[h] = Peer(h, addr[0], int(p))
            print(f"[+] {h} beigetreten: {addr[0]}:{p}")

        elif msg.startswith("LEAVE"):
            _, h = msg.split()
            if h in peers:
                del peers[h]
            print(f"[-] {h} hat den Chat verlassen.")

# Socket einrichten
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
udp_sock.bind(("", udp_port))

send_join()
print(f"[{handle}] UDP-Netzwerk läuft auf Port {udp_port}...")

try:
    receive_loop()
except KeyboardInterrupt:
    send_leave()
    print(f"[{handle}] Netzwerkmodul beendet.")
    udp_sock.close()
