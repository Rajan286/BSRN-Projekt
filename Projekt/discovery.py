import threading
import time
from common import create_fifo, load_config, write_pid, log
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