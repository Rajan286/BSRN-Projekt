#!/usr/bin/env bash
##
## @file start_chat.sh
## @brief Startskript zum sequentiellen Starten der SLCP-Komponenten.
##
## Dieses Skript startet die drei Hauptkomponenten des SLCP-Chat-Programms:
## 1) Discovery-Dienst
## 2) Netzwerk-Modul
## 3) Kommandozeilen-UI
##
## @section usage Verwendung
##   chmod +x start_chat.sh
##   ./start_chat.sh
##
## @section cleanup Aufräumroutinen
##   Beim Empfang von SIGINT oder SIGTERM werden alle gestarteten Prozesse sauber beendet.
##

# Funktion zum Aufräumen: Stoppt alle Hintergrundprozesse
cleanup() {
  echo "🔴 Stoppe alle Komponenten..."
  kill "$DISC_PID" "$NET_PID" 2>/dev/null
  exit 0
}

# Signal-Handler registrieren
trap cleanup SIGINT SIGTERM EXIT

# 1) Discovery starten (Hintergrund)
echo "🟢 Starte Discovery-Dienst..."
python3 discovery.py config.toml &
DISC_PID=$!
sleep 1  # Warten, bis Discovery initialisiert ist

# 2) Netzwerk-Modul starten (Hintergrund)
echo "🟢 Starte Netzwerk-Modul..."
python3 network.py config.toml &
NET_PID=$!
sleep 1  # Warten, bis Netzwerk-Modul bereit ist

# 3) UI starten (Vordergrund)
echo "🟢 Starte Chat-UI..."
python3 ui.py

# Sobald UI beendet wird, wird cleanup durch den trap-Handler aufgerufen