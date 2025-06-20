"""
@file discovery.py
@brief Implementierung des Discovery-Dienstes für das SLCP-Chat-Programm.

Die Klasse Discovery verwaltet eingehende WHO-, JOIN- und LEAVE-Anfragen via UDP
und kommuniziert mit der UI über Named Pipes (FIFOs). Sie speichert bekannte Peers
und antwortet auf Broadcasts mit aktuellen Benutzer-Informationen.
"""

import socket  #: Modul für Netzwerk-Sockets
import threading  #: Threading für parallele Verarbeitung
import time  #: Zeitfunktionen (sleep)
import signal  #: Signal-Handling (SIGINT)
from common import (
    load_config,    #: Config-Einlesefunktion
    create_fifo,    #: FIFO-Erstellung
    read_from_fifo, #: FIFO-Lese-Funktion
    write_to_fifo,  #: FIFO-Schreib-Funktion (falls UI ansprechbar)
    write_pid,      #: PID-File schreiben
    remove_pid,     #: PID-File löschen
    log             #: Logger
)
from peer import Peer  #: Peer-Klasse mit Handle, IP und Port

# FIFO-Namen zur Kommunikation zwischen UI und Discovery
FIFO_UI_TO_DISC = "ui_to_discovery"
FIFO_DISC_TO_UI = "discovery_to_ui"


class Discovery:
    """
    @brief Discovery-Dienst-Klasse

    Diese Klasse startet zwei Threads:
    - listen_to_ui: Lauscht auf WHO-Anfragen von der UI
    - listen_udp_all: Lauscht auf UDP-Broadcasts und Nachrichten

    @param config_path Pfad zur TOML-Konfigurationsdatei.
    """

    def __init__(self, config_path="config.toml"):
        # Konfiguration laden
        self.config = load_config(config_path)
        self.handle = self.config["handle"]  #: Eigener Benutzername
        self.port = self.config["port"]  #: Eigener UDP-Port
        self.whois_port = self.config.get("whoisport", 4000)  #: Discovery-Port
        
        # Bekannte Peers initialisieren mit eigenem Peer-Eintrag
        self.known_peers = {}
        self.known_peers[self.handle] = Peer(self.handle, "255.255.255.255", self.port)

        # FIFOs für UI-Kommunikation erstellen
        create_fifo(FIFO_UI_TO_DISC)
        create_fifo(FIFO_DISC_TO_UI)
        write_pid()  #: PID-File für Prozessverwaltung

        # Listener-Threads definieren
        self.listen_ui_thread = threading.Thread(
            target=self.listen_to_ui, daemon=True
        )
        self.udp_listener_thread = threading.Thread(
            target=self.listen_udp_all, daemon=True
        )

    def start(self):
        """
        @brief Startet beide Listener-Threads und hält den Dienst aktiv.

        @return None
        """
        self.listen_ui_thread.start()
        self.udp_listener_thread.start()
        log.info("Discovery-Dienst gestartet.")
        while True:
            time.sleep(1)  #: Haupt-Thread schläft endlos

    def listen_to_ui(self):
        """
        @brief Thread-Funktion: Lauscht auf FIFO-Nachrichten von der UI.

        - Bei Nachricht 'WHO' wird send_who() aufgerufen.

        @return None
        """
        while True:
            msg = read_from_fifo(FIFO_UI_TO_DISC, blocking=True)
            if msg == "WHO":
                self.send_who()

    def send_who(self):
        """
        @brief Sendet eine WHO-Broadcast-Anfrage an alle Discovery-Server.

        @return None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b"WHO\n", ("255.255.255.255", self.whois_port))
        #log.info("WHO gesendet.")
        sock.close()

    def listen_udp_all(self):
        """
        @brief Thread-Funktion: Lauscht auf UDP-Nachrichten aller SLCP-Befehle.

        - WHO: Antwort mit KNOWNUSERS
        - JOIN: Fügt neuen Peer hinzu
        - LEAVE: Entfernt Peer

        @return None
        """
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
                #log.info(f"Antwort auf WHO an {addr}: {response.strip()}")

            elif msg.startswith("JOIN"):
                try:
                    _, handle, port_str = msg.split()
                    port = int(port_str)
                    self.known_peers[handle] = Peer(handle, addr[0], port)
                    #log.info(f"JOIN empfangen von {handle}@{addr[0]}:{port}")
                except Exception as e:
                    log.warning(f"Fehler bei JOIN-Verarbeitung: {e}")

            elif msg.startswith("LEAVE"):
                try:
                    _, handle = msg.split()
                    if handle in self.known_peers:
                        del self.known_peers[handle]
                        #log.info(f"LEAVE empfangen: {handle} wurde entfernt.")
                except Exception as e:
                    log.warning(f"Fehler bei LEAVE-Verarbeitung: {e}")

    def shutdown(self, *args):  # pylint: disable=unused-argument
        """
        @brief Beendet den Discovery-Dienst und entfernt die PID-Datei.

        @return None
        """
        remove_pid()
        log.info("Discovery-Dienst beendet.")
        exit(0)


if __name__ == "__main__":
    d = Discovery()
    signal.signal(signal.SIGINT, d.shutdown)
    d.start()
