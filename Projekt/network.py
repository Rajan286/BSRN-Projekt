"""
@file network.py
@brief Implementierung der Netzwerk-Kommunikation für das SLCP-Chat-Programm.

Dieses Modul kümmert sich um das Senden und Empfangen von SLCP-Nachrichten:
- Broadcast (JOIN, LEAVE, WHO)
- Unicast (MSG, IMG, WHOIS, KNOWNUSERS)
Es verwendet UDP für Broadcasts und TCP für Peer-to-Peer-Kommunikation.
"""

import socket  #: Netzwerk-Sockets (UDP/TCP)
import threading  #: Threads für gleichzeitige Listener
import os  #: Betriebssystemfunktionen (Dateisystem)
import time  #: Zeitfunktionen (sleep, time)
import sys  #: Systemfunktionen (Exit)
import signal  #: Signal-Handling (SIGINT/SIGTERM)
from common import (
    load_config,    #: Konfigurationsdatei einlesen
    create_fifo,    #: FIFO-Erstellung für UI-Kommunikation
    read_from_fifo, #: FIFO-Lese-Funktion
    write_to_fifo   #: FIFO-Schreib-Funktion
)
from peer import Peer  #: Peer-Klasse mit Handle, IP und Port

# FIFO-Namen zur Kommunikation zwischen UI und Netzwerk-Modul
FIFO_UI_TO_NET = "ui_to_net"
FIFO_NET_TO_UI = "net_to_ui"

# Globale Variablen für Peers und Netzwerk
peers = {}  #: Dictionary aller bekannten Peers
udp_sock = None  #: UDP-Socket für Broadcasts
config = {}  #: Geladene Konfiguration
running = True  #: Steuerungsschalter für Listener-Loops
last_peers_display = set()  #: Merkt sich zuletzt angezeigte Peers


def get_own_ip(peer_ip="8.8.8.8"):
    """
    @brief Ermittelt die eigene lokale IP-Adresse.

    Baut eine temporäre UDP-Verbindung zu 'peer_ip' auf und liest
    die lokale Socket-Adresse aus.

    @param peer_ip Externe IP-Adresse zum Herstellen der Verbindung.
    @return String mit der lokalen IP-Adresse oder '127.0.0.1' bei Fehler.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect((peer_ip, 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def send_join(handle, port):
    """
    @brief Sendet eine JOIN-Nachricht per UDP-Broadcast und TCP-Unicast.

    Verteilt die Nachricht an Broadcast und an bereits bekannte Peers.

    @param handle Eigenes Handle.
    @param port Eigener UDP-Port.
    @return None
    """
    msg = f"JOIN {handle} {port}\n"
    try:
        udp_sock.sendto(msg.encode(), ("255.255.255.255", 4000))
        for peer in peers.values():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(peer.get_address())
                s.sendall(msg.encode())
    except Exception:
        pass


def send_leave(handle):
    """
    @brief Sendet eine LEAVE-Nachricht an alle Teilnehmer.

    @param handle Eigenes Handle.
    @return None
    """
    msg = f"LEAVE {handle}\n"
    try:
        udp_sock.sendto(msg.encode(), ("255.255.255.255", 4000))
        for peer in peers.values():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(peer.get_address())
                s.sendall(msg.encode())
    except Exception:
        pass


def send_who():
    """
    @brief Sendet eine WHO-Broadcast-Anfrage.

    @return None
    """
    try:
        udp_sock.sendto(b"WHO\n", ("255.255.255.255", 4000))
    except Exception:
        pass


def send_whois(target_handle):
    """
    @brief Sendet eine WHOIS-Anfrage an einen spezifischen Peer.

    @param target_handle Handle des Ziels.
    @return None
    """
    peer = peers.get(target_handle)
    if not peer:
        write_to_fifo(FIFO_NET_TO_UI, f"⚠️ Kein Peer mit Handle '{target_handle}' bekannt.")
        return
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(peer.get_address())
            msg = f"WHOIS {target_handle}\n"
            s.sendall(msg.encode())
            response = s.recv(1024).decode().strip()
            if response.startswith("IAM"):
                write_to_fifo(FIFO_NET_TO_UI, f"✅ {response}")
    except Exception:
        write_to_fifo(FIFO_NET_TO_UI, f"❌ WHOIS fehlgeschlagen.")


def send_msg(target, text):
    """
    @brief Sendet eine Textnachricht (MSG) an einen Peer.

    @param target Handle des Empfängers.
    @param text Nachrichtentext.
    @return None
    """
    peer = peers.get(target)
    if not peer:
        return
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(peer.get_address())
            msg = f"MSG {config['handle']} {text}\n"
            s.sendall(msg.encode())
    except Exception:
        pass

def send_img(target, image_path):
    """
    @brief Sendet eine Bildnachricht (IMG) an einen Peer.

    @param target Handle des Empfängers.
    @param image_path Pfad zur Bilddatei.
    @return None
    """
    peer = peers.get(target)
    if not peer or not os.path.exists(image_path):
        return
    size = os.path.getsize(image_path)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(peer.get_address())
            s.sendall(f"IMG {config['handle']} {size}\n".encode())
            with open(image_path, "rb") as f:
                s.sendfile(f)
    except Exception:
        pass

