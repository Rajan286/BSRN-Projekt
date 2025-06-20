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


def receive_udp():
    """
    @brief Listener-Loop für eingehende UDP-Nachrichten (JOIN/LEAVE/IAM/KNOWNUSERS).

    Schreibt entsprechende Events in die UI-FIFO und aktualisiert Peers-Listen.

    @return None
    """
    global last_peers_display
    while running:
        try:
            data, addr = udp_sock.recvfrom(1024)
        except Exception:
            break
        msg = data.decode().strip()
        if msg.startswith("JOIN"):
            _, handle, port = msg.split()
            peers[handle] = Peer(handle, addr[0], int(port))
            write_to_fifo(FIFO_NET_TO_UI, f"🔵 {handle} ist dem Chat beigetreten.")
        elif msg.startswith("LEAVE"):
            _, handle = msg.split()
            peers.pop(handle, None)
            write_to_fifo(FIFO_NET_TO_UI, f"🚪 {handle} hat den Chat verlassen.")
        elif msg.startswith("IAM"):
            _, handle, ip, port = msg.split()
            peers[handle] = Peer(handle, ip, int(port))
        elif msg.startswith("KNOWNUSERS"):
            known = msg[len("KNOWNUSERS "):].split(",")
            updated = []
            for entry in known:
                parts = entry.strip().split()
                if len(parts) == 3:
                    h, ip, p = parts
                    peers[h] = Peer(h, ip, int(p))
                    updated.append(h)
            updated_set = set(updated)
            if updated and updated_set != last_peers_display:
                write_to_fifo(FIFO_NET_TO_UI, f"✅ Bekannte Nutzer: {', '.join(updated)}")
                last_peers_display = updated_set
            elif not updated:
                write_to_fifo(FIFO_NET_TO_UI, "⚠️ Keine bekannten Nutzer empfangen.")


def listen_tcp(port, imagepath):
    """
    @brief TCP-Server-Loop für Unicast-Kommunikation (MSG, IMG, WHOIS, JOIN, LEAVE, WHO).

    @param port Eigener TCP-Port (gleich UDP-Port).
    @param imagepath Verzeichnis zum Speichern empfangener Bilder.
    @return None
    """
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.settimeout(1.0)
    srv.bind(("", port))
    srv.listen()
    while running:
        try:
            conn, addr = srv.accept()
        except socket.timeout:
            continue
        except Exception:
            break
        with conn:
            data = b""
            while not data.endswith(b"\n"):
                chunk = conn.recv(1)
                if not chunk:
                    break
                data += chunk
            data = data.decode().strip()

            if data.startswith("MSG"):
                _, sender, text = data.split(" ", 2)
                write_to_fifo(FIFO_NET_TO_UI, f"[{sender}] {text}")
                if sender not in peers:
                    peers[sender] = Peer(sender, addr[0], sys.maxsize)
                auto = config.get("autoreply", "").strip()
                if auto and "[AutoReply]" not in text and sender != config["handle"]:
                    send_msg(sender, f"[AutoReply] {auto}")

            elif data.startswith("IMG"):
                try:
                    _, sender, size = data.split()
                    size = int(size)
                    os.makedirs(imagepath, exist_ok=True)
                    filepath = os.path.join(imagepath, f"{sender}_{int(time.time())}.jpg")
                    with open(filepath, "wb") as f:
                        received = 0
                        while received < size:
                            chunk = conn.recv(min(4096, size - received))
                            if not chunk:
                                break
                            f.write(chunk)
                            received += len(chunk)
                    if received == size:
                        write_to_fifo(FIFO_NET_TO_UI, f"[{sender}] 📷 Bild ({size} Bytes) gespeichert: {filepath}")
                    else:
                        write_to_fifo(FIFO_NET_TO_UI, f"[{sender}] ⚠️ Bild unvollständig empfangen ({received}/{size} Bytes): {filepath}")
                    if sender not in peers:
                        peers[sender] = Peer(sender, addr[0], sys.maxsize)
                    auto = config.get("autoreply", "").strip()
                    if auto and sender != config["handle"]:
                        send_msg(sender, f"[AutoReply] {auto}")
                except Exception:
                    write_to_fifo(FIFO_NET_TO_UI, f"❌ Fehler beim Empfang des Bilds.")

            elif data.startswith("WHOIS"):
                _, target = data.split()
                if target == config["handle"]:
                    local_ip = get_own_ip(addr[0])
                    response = f"IAM {config['handle']} {local_ip} {config['port']}\n"
                    conn.sendall(response.encode())

            elif data.startswith("JOIN"):
                _, handle, port = data.split()
                write_to_fifo(FIFO_NET_TO_UI, f"🔵 {handle} ist dem Chat beigetreten.")

            elif data.startswith("LEAVE"):
                _, handle = data.split()
                write_to_fifo(FIFO_NET_TO_UI, f"🚪 {handle} hat den Chat verlassen.")
                peers.pop(handle, None)

            elif data.startswith("WHO"):
                local_ip = get_own_ip(addr[0])
                entries = ([f"{config['handle']} {local_ip} {config['port']}"] +
                           [f"{h} {p.ip} {p.port}" for h, p in peers.items()])
                response = "KNOWNUSERS " + ", ".join(entries) + "\n"
                conn.sendall(response.encode())


def handle_commands(handle, port, imagepath):
    """
    @brief Verarbeitet Befehle von der UI-FIFO und ruft entsprechende Funktionen auf.

    Unterstützte Befehle:
    - msg <target> <text>
    - img <target> <path>
    - who, whois <handle>
    - JOIN <handle> <port>
    - LEAVE
    - exit

    @param handle Eigenes Handle.
    @param port Eigener Port (UDP/TCP).
    @param imagepath Verzeichnis für Bilder.
    @return None
    """
    global running
    create_fifo(FIFO_UI_TO_NET)
    while running:
        try:
            cmd = read_from_fifo(FIFO_UI_TO_NET)
            if not cmd:
                time.sleep(0.1)
                continue
            if cmd.startswith("msg "):
                _, target, text = cmd.split(" ", 2)
                send_msg(target, text)
            elif cmd.startswith("img "):
                _, target, path = cmd.split(" ", 2)
                send_img(target, path)
            elif cmd == "who":
                send_who()
            elif cmd.startswith("whois "):
                _, h = cmd.split(" ", 1)
                send_whois(h)
            elif cmd.startswith("JOIN "):
                _, h, p = cmd.split()
                send_join(h, int(p))
            elif cmd == "LEAVE":
                send_leave(handle)
            elif cmd == "exit":
                send_leave(handle)
                running = False
                try:
                    udp_sock.close()
                except Exception:
                    pass
                time.sleep(0.5)
                os._exit(0)
        except Exception:
            pass


def cleanup_and_exit(signum, frame):  # pylint: disable=unused-argument
    """
    @brief Signal-Handler für SIGINT/SIGTERM, sendet LEAVE und beendet das Programm.

    @param signum Signalnummer.
    @param frame Aktueller Stack-Frame.
    @return None
    """
    send_leave(config.get("handle", ""))
    os._exit(0)

# Signal-Handler registrieren
signal.signal(signal.SIGINT, cleanup_and_exit)
signal.signal(signal.SIGTERM, cleanup_and_exit)


def start_network():
    """
    @brief Initialisiert das Netzwerk-Modul und startet Listener-Threads.

    Lädt Konfiguration, baut Sockets, startet Broadcast/Unicast-Listeners
    und verarbeitet UI-Befehle.

    @return None
    """
    global udp_sock, config
    config = load_config()
    handle = config["handle"]
    port = config["port"]
    imagepath = config.get("imagepath", "images")
    os.makedirs(imagepath, exist_ok=True)
    create_fifo(FIFO_NET_TO_UI)

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.bind(("", port))

    send_join(handle, port)

    threading.Thread(target=receive_udp, daemon=True).start()
    threading.Thread(target=listen_tcp, args=(port, imagepath), daemon=True).start()
    handle_commands(handle, port, imagepath)


if __name__ == "__main__":
    start_network()