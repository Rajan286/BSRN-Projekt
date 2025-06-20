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