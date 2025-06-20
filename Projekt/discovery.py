import socket
import threading
import time
from common import create_fifo, load_config, read_from_fifo, write_pid, log
from peer import Peer

FIFO_UI_TO_DISC = "ui_to_discovery"
FIFO_DISC_TO_UI = "discovery_to_ui"

class Discovery:
    """
    Discovery-Dienst, der auf WHO-Nachrichten antwortet
    und JOIN/LEAVE verarbeitet.
    """
    def __init__(self, config_path="config.toml"):
        self.config = load_config(config_path)
        self.handle = self.config["handle"]
        self.port = self.config["port"]
        self.whois_port = self.config.get("whoisport", 4000)
        self.known_peers = {}
        self.known_peers[self.handle] = Peer(self.handle, "255.255.255.255", self.port)

        self.listen_ui_thread = threading.Thread(target=self.listen_to_ui, daemon=True)
        self.udp_listener_thread = threading.Thread(target=self.listen_udp_all, daemon=True)

        create_fifo(FIFO_UI_TO_DISC)
        create_fifo(FIFO_DISC_TO_UI)
        write_pid()
        
    def start(self):
        self.listen_ui_thread.start()
        self.udp_listener_thread.start()
        log.info("Discovery-Dienst gestartet.")
        while True:
            time.sleep(1)

    def listen_to_ui(self):
        while True:
            msg = read_from_fifo(FIFO_UI_TO_DISC, blocking=True)
            if msg == "WHO":
                self.send_who()
    
    def listen_udp_all(self):
       
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.whois_port))
        while True:
            data, addr = sock.recvfrom(1024)
            msg = data.decode().strip()

            if msg == "WHO":
                # Antwort zusammenstellen
                response = (
                    "KNOWNUSERS " + ", ".join(
                        [f"{peer.handle} {peer.ip} {peer.port}" for peer in self.known_peers.values()]
                    ) + "\n"
                )
                sock.sendto(response.encode(), addr)
                log.info(f"Antwort auf WHO an {addr}: {response.strip()}")

            elif msg.startswith("JOIN"):
                try:
                    _, handle, port_str = msg.split()
                    port = int(port_str)
                    self.known_peers[handle] = Peer(handle, addr[0], port)
                    log.info(f"JOIN empfangen von {handle}@{addr[0]}:{port}")
                except Exception as e:
                    log.warning(f"Fehler bei JOIN-Verarbeitung: {e}")

            elif msg.startswith("LEAVE"):
                try:
                    _, handle = msg.split()
                    if handle in self.known_peers:
                        del self.known_peers[handle]
                        log.info(f"LEAVE empfangen: {handle} wurde entfernt.")
                except Exception as e:
                    log.warning(f"Fehler bei LEAVE-Verarbeitung: {e}")            