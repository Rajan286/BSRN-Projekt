"""
@file common.py
@brief Utility-Funktionen und IPC-/Logging-Infrastruktur für den SLCP-Discovery-Dienst.

Diese Datei stellt Hilfsfunktionen, globale Konstanten und Pipe-Verwaltung bereit.
"""

import os  #: Betriebssystemfunktionen
import sys  #: Systemfunktionen (z.B. Exit)
import errno  #: Errno-Konstanten für Fehlercodes
import toml  #: Einlesen von TOML-Konfigurationsdateien
import signal  #: Signal-Handling (z.B. SIGINT)
import logging  #: Logging-Framework
import getpass  #: Ermittlung des aktuellen Benutzers
import time  #: Zeitfunktionen (sleep)

# Globale Konstanten und Konfiguration
USER = getpass.getuser()  #: Aktueller Benutzername
PIPE_DIR = f"/tmp/slcp_{USER}"  #: Verzeichnis für Named Pipes (FIFOs)
os.makedirs(PIPE_DIR, exist_ok=True)  #: Erstelle das Verzeichnis, falls es nicht existiert

PID_FILE = os.path.join(PIPE_DIR, "slcp_discovery.pid")  #: Pfad zur PID-Datei des Discovery-Dienstes

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
log = logging.getLogger("SLCP")  #: Logger für SLCP-Ausgaben


def load_config(config_path="config.toml"):  # pylint: disable=redefined-outer-name
    """
    @brief Liest die Konfiguration aus einer TOML-Datei.

    Diese Funktion lädt die Datei 'config.toml' und gibt den Abschnitt 'DEFAULT' zurück.
    @param config_path Pfad zur TOML-Konfigurationsdatei.
    @return Dictionary mit Werten aus dem Abschnitt 'DEFAULT'.
    @throws SystemExit Wenn die Datei nicht existiert oder nicht gelesen werden kann.
    """
    if not os.path.exists(config_path):
        log.error(f"Konfigurationsdatei {config_path} fehlt.")
        sys.exit(1)
    with open(config_path, "r") as f:
        return toml.load(f).get('DEFAULT', {})


def pipe_path(name):
    """
    @brief Bestimmt den Pfad zur FIFO für einen gegebenen Prozessnamen.

    @param name Name der Pipe (z.B. 'ui', 'network').
    @return Vollständiger Pfad zur Named Pipe im PIPE_DIR.
    """
    return os.path.join(PIPE_DIR, f"{name}.pipe")


def create_fifo(name):
    """
    @brief Erstellt eine Named Pipe (FIFO), falls sie nicht existiert.

    @param name Name der Pipe, die erstellt werden soll.
    @return Pfad zur erstellten oder bereits existierenden Pipe.
    """
    path = pipe_path(name)
    if not os.path.exists(path):
        try:
            os.mkfifo(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    return path


def write_to_fifo(name, message):
    """
    @brief Schreibt eine Nachricht in eine Named Pipe.

    Versucht bis zu 5 Mal, non-blocking in die FIFO zu schreiben, und
    ignoriert Broken-Pipe-Fehler oder fehlende Leser.

    @param name Name der Pipe.
    @param message Zu schreibende Nachricht (String).
    @return None
    """
    path = pipe_path(name)

    if not os.path.exists(path):
        # FIFO existiert nicht → ignorieren
        return

    for attempt in range(5):
        try:
            fifo_fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
            with os.fdopen(fifo_fd, 'w') as fifo:
                fifo.write(message + "\n")
            return
        except OSError as e:
            if e.errno in (errno.ENXIO, errno.EPIPE):
                time.sleep(0.2)
            else:
                log.warning(f"Fehler beim Schreiben in FIFO {path}: {e}")
                return


def read_from_fifo(name, blocking=True):
    """
    @brief Liest eine Zeile aus einer Named Pipe.

    @param name Name der Pipe.
    @param blocking Wenn False, wird non-blocking gelesen.
    @return Geladene Zeile als String (ohne Newline) oder leer bei Fehler.
    """
    path = pipe_path(name)
    flags = os.O_RDONLY
    if not blocking:
        flags |= os.O_NONBLOCK
    try:
        fd = os.open(path, flags)
        with os.fdopen(fd) as fifo:
            return fifo.readline().strip()
    except Exception as e:
        log.warning(f"Fehler beim Lesen aus FIFO {path}: {e}")
        return ""


def write_pid(pid_file=PID_FILE):
    """
    @brief Schreibt die aktuelle Prozess-ID in eine Datei.

    @param pid_file Pfad zur PID-Datei.
    @return None
    """
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        log.error(f"Fehler beim Schreiben der PID-Datei: {e}")
        sys.exit(1)


def remove_pid(pid_file=PID_FILE):
    """
    @brief Entfernt die PID-Datei des Discovery-Dienstes.

    @param pid_file Pfad zur zu entfernenden PID-Datei.
    @return None
    """
    try:
        os.remove(pid_file)
    except Exception as e:
        log.warning(f"Fehler beim Entfernen der PID-Datei: {e}")


def graceful_shutdown(sig, frame):  # pylint: disable=unused-argument
    """
    @brief Signal-Handler für SIGINT, beendet das Programm sauber.

    @param sig Signalnummer (z.B. signal.SIGINT).
    @param frame Aktueller Stack-Frame (wird nicht genutzt).
    @return None
    """
    log.info("SIGINT empfangen. Beende Programm.")
    sys.exit(0)