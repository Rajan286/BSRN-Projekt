import os
import sys
import toml
import getpass

# Benutzer- und Verzeichnispfade
USER = getpass.getuser()
PIPE_DIR = f"/tmp/slcp_{USER}"
os.makedirs(PIPE_DIR, exist_ok=True)

PID_FILE = os.path.join(PIPE_DIR, "slcp_discovery.pid")

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
