"""
@file ui.py
@brief Implementierung der Kommandozeilen-Benutzeroberfläche (CLI) für das SLCP-Chat-Programm.

Die Klasse ChatUI bietet eine textbasierte Oberfläche zum Senden von Befehlen
und Anzeigen von Nachrichten/Broadcasts. Kommunikation mit dem Netzwerk-Modul erfolgt
über Named Pipes (FIFOs).
"""

import threading  #: Threading für asynchrone FIFO-Lesesessions
import time  #: Zeitfunktionen (sleep)
import os  #: Betriebssystemfunktionen (Dateisystem)
from common import (
    load_config,    #: Einlesen der Konfiguration
    create_fifo,    #: FIFO-Erstellung für UI-Kommunikation
    write_to_fifo,  #: FIFO-Schreib-Funktion
    pipe_path       #: Ermittlung des FIFO-Pfads
)

# FIFO-Namen zur Kommunikation zwischen UI und Netzwerk
FIFO_UI_TO_NET = "ui_to_net"
FIFO_NET_TO_UI = "net_to_ui"


class ChatUI:
    """
    @brief Chat-Interface für den Benutzer.

    Initialisiert UI-Pipes, lädt Konfiguration und bietet eine Eingabe-Loop für Befehle.
    """
    def __init__(self):
        """
        @brief Initialisiert das ChatUI-Objekt.

        Lädt Konfiguration, legt Named Pipes an und speichert Pfad zur Eingabe-Pipe.
        """
        self.config = load_config()  #: Geladene Konfiguration
        self.handle = self.config["handle"]  #: Eigener Benutzername
        self.port = self.config["port"]      #: Eigener Netzwerkport

        create_fifo(FIFO_UI_TO_NET)    #: Pipe für UI→Netzwerk
        create_fifo(FIFO_NET_TO_UI)    #: Pipe für Netzwerk→UI
        self.pipe_path = pipe_path(FIFO_NET_TO_UI)  #: Pfad der UI-Leser-Pipe
        
    def listen_pipes(self):
        """
        @brief Liest dauerhaft Nachrichten aus der FIFO der Netzwerk-Komponente.

        Öffnet die UI-Leser-Pipe und gibt neue Nachrichten in der Konsole aus.
        """
        try:
            with open(self.pipe_path, 'r') as fifo:
                while True:
                    msg = fifo.readline().strip()
                    if msg:
                        print(msg)
        except Exception as e:
            print(f"[UI] Fehler beim Öffnen/Lesen von FIFO: {e}")

    def start(self):
        """
        @brief Startet die UI-Hauptschleife und den Pipe-Listener-Thread.

        Zeigt Willkommensnachricht und Eingabe-Prompt an und verarbeitet Nutzerbefehle.
        """
        print(f"\n👋 Willkommen im SLCP-Chat, {self.handle}!")
        print("🔹 Gib `help` ein, um alle Befehle anzuzeigen.\n")

        # Asynchroner Listener-Thread für eingehende Nachrichten
        threading.Thread(target=self.listen_pipes, daemon=True).start()
        time.sleep(0.2)  #: Kurze Pause, damit FIFO bereit ist

        # Haupt-Eingabe-Loop
        while True:
            try:
                cmd = input("> ").strip()
                if cmd == "help":
                    print("🔧 Verfügbare Befehle:")
                    print("  join                     - Chat beitreten")
                    print("  who                      - Liste der Nutzer abfragen")
                    print("  whois <Handle>           - Details zu Handle anfragen")
                    print("  msg <User> <Text>        - Textnachricht senden")
                    print("  img <User> <Pfad>        - Bild senden")
                    print("  leave                    - Chat verlassen und schließen")
                elif cmd.startswith(("msg ", "img ", "whois ")):
                    write_to_fifo(FIFO_UI_TO_NET, cmd)
                elif cmd == "who":
                    write_to_fifo(FIFO_UI_TO_NET, "who")
                elif cmd == "join":
                    join_msg = f"JOIN {self.handle} {self.port}"
                    write_to_fifo(FIFO_UI_TO_NET, join_msg)
                    print("🔁 JOIN gesendet.")
                elif cmd == "leave":
                    # Endgültiger Austritt
                    write_to_fifo(FIFO_UI_TO_NET, "LEAVE")
                    print("👋 Auf Wiedersehen!")
                    break
                else:
                    print("❌ Unbekannter Befehl. Gib `help` ein für eine Liste.")
            except KeyboardInterrupt:
                print("\n⚠️  Mit STRG+C beendet.")
                break


if __name__ == "__main__":
    ChatUI().start()