"""
@file discovery.py
@brief Implementierung des Discovery-Dienstes für das SLCP-Chat-Programm.

Die Klasse Discovery verwaltet eingehende WHO-, JOIN- und LEAVE-Anfragen via UDP.
Sie speichert bekannte Peers und antwortet auf Broadcasts mit aktuellen Benutzer-Informationen.
"""

import socket  #: Modul für Netzwerk-Sockets
import threading  #: Threading für parallele Verarbeitung
import time  #: Zeitfunktionen (sleep)
import signal  #: Signal-Handling (SIGINT)
from common import (
    load_config,    #: Config-Einlesefunktion
    write_pid,      #: PID-File schreiben
    remove_pid,     #: PID-File löschen
    log             #: Logger
)
from peer import Peer  #: Peer-Klasse mit Handle, IP und Port

class Discovery:
    """
    Discovery-Dienst-Klasse

    Startet einen Thread, der auf alle relevanten SLCP-Befehle via UDP lauscht.
    """
    def __init__(self, config_path="config.toml"):
        # Konfiguration laden und Peer-Liste initialisieren
        self.config = load_config(config_path)
        self.handle = self.config["handle"]  #: Eigener Benutzername
        self.port = self.config["port"]  #: Eigener UDP-Port
        self.whois_port = self.config.get("whoisport", 4000)  #: Discovery-Port
        self.known_peers = {}
        self.known_peers[self.handle] = Peer(self.handle, "255.255.255.255", self.port)
        write_pid()
        self.udp_listener_thread = threading.Thread(
            target=self.listen_udp_all, daemon=True
        )

    def start(self):
        """
        Startet den Discovery-Listener-Thread und hält den Dienst aktiv.
        """
        self.udp_listener_thread.start()
        log.info("Discovery-Dienst gestartet.")
        while True:
            time.sleep(1)

    def send_who(self):
        """
        Sendet eine WHO-Broadcast-Anfrage an alle Discovery-Server.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b"WHO\n", ("255.255.255.255", self.whois_port))
        sock.close()

    def listen_udp_all(self):
        """
        Lauscht auf UDP-Nachrichten aller SLCP-Befehle:

        - WHO: Antwortet mit aktueller Peerliste.
        - JOIN: Fügt neuen Peer hinzu und leitet JOIN an andere weiter.
        - LEAVE: Entfernt Peer und leitet LEAVE an andere weiter.

        @return None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.whois_port))
        while True:
            data, addr = sock.recvfrom(1024)
            msg = data.decode().strip()

            if msg == "WHO":
                # Antwort mit allen bekannten Nutzern senden
                response = (
                    "KNOWNUSERS " + ", ".join(
                        [f"{p.handle} {p.ip} {p.port}" for p in self.known_peers.values()]
                    ) + "\n"
                )
                sock.sendto(response.encode(), addr)

            elif msg.startswith("JOIN"):
                # Peer zur Liste hinzufügen und JOIN an andere weiterleiten
                try:
                    _, handle, port_str = msg.split()
                    port = int(port_str)
                    self.known_peers[handle] = Peer(handle, addr[0], port)
                except Exception as e:
                    log.warning(f"Fehler bei JOIN-Verarbeitung: {e}")
                for peer_handle, peer in self.known_peers.items():
                    if peer_handle != handle:
                        try:
                            sock.sendto(data, (peer.ip, peer.port))
                        except PermissionError:
                            continue

            elif msg.startswith("LEAVE"):
                # Peer entfernen und LEAVE an andere weiterleiten
                try:
                    _, handle = msg.split()
                    if handle in self.known_peers:
                        del self.known_peers[handle]
                except Exception as e:
                    log.warning(f"Fehler bei LEAVE-Verarbeitung: {e}")
                for peer_handle, peer in self.known_peers.items():
                    if peer_handle != handle:
                        try:
                            sock.sendto(data, (peer.ip, peer.port))
                        except PermissionError:
                            continue

    def shutdown(self, *args):  # pylint: disable=unused-argument
        """
        Beendet den Discovery-Dienst und entfernt die PID-Datei.
        """
        remove_pid()
        log.info("Discovery-Dienst beendet.")
        exit(0)

if __name__ == "__main__":
    d = Discovery()
    signal.signal(signal.SIGINT, d.shutdown)
    d.start()
