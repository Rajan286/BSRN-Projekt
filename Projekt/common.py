import os
import sys
import toml
import getpass
import errno
import signal
import logging
import time

# Benutzer- und Verzeichnispfade
USER = getpass.getuser()
PIPE_DIR = f"/tmp/slcp_{USER}"
os.makedirs(PIPE_DIR, exist_ok=True)

PID_FILE = os.path.join(PIPE_DIR, "slcp_discovery.pid")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
log = logging.getLogger("SLCP")

def load_config(config_path="config.toml"):
    """
    Lädt die Konfigurationsdatei und gibt die DEFAULT-Sektion zurück.
    """
    if not os.path.exists(config_path):
        log.error(f"Konfigurationsdatei {config_path} fehlt.")
        sys.exit(1)
    with open(config_path, "r") as f:
        return toml.load(f)['DEFAULT']

def pipe_path(name):
    """
    Liefert den Pfad zur benannten Pipe (FIFO) für den gegebenen Namen.
    """
    return os.path.join(PIPE_DIR, f"{name}.pipe")
def create_fifo(name):
    """
    Erstellt eine benannte Pipe (FIFO), falls sie noch nicht existiert.
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
    Schreibt eine Nachricht in die benannte Pipe. Versucht es bis zu 5x.
    """
    path = pipe_path(name)
    if not os.path.exists(path):
        return

    for attempt in range(5):
        try:
            fifo_fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
            with os.fdopen(fifo_fd, 'w') as fifo:
                fifo.write(message + "\n")
            return
        except OSError as e:
            if e.errno in (6, 32):  # Kein Leser / Broken pipe
                time.sleep(0.2)
            else:
                log.warning(f"Fehler beim Schreiben in FIFO {path}: {e}")
                return
    return

def read_from_fifo(name, blocking=True):
    """
    Liest eine Nachricht aus der benannten Pipe. Optional nicht-blockierend.
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
    Schreibt die aktuelle PID in eine Datei zur späteren Prozesskontrolle.
    """
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        log.error(f"Fehler beim Schreiben der PID-Datei: {e}")
        sys.exit(1)

def remove_pid(pid_file=PID_FILE):
    """
    Entfernt die PID-Datei, z. B. beim Shutdown.
    """
    try:
        os.remove(pid_file)
    except Exception as e:
        log.warning(f"Fehler beim Entfernen der PID-Datei: {e}")

def graceful_shutdown(signal, frame):
    """
    Reagiert auf SIGINT (z. B. STRG+C) mit sauberem Programmende.
    """
    log.info("SIGINT empfangen. Beende Programm.")
    sys.exit(0)