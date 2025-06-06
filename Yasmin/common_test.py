import os
import toml
import time

PIPE_DIR = "/tmp/slcp_bileya"
os.makedirs(PIPE_DIR, exist_ok=True)

def pipe_path(name):
    return os.path.join(PIPE_DIR, f"{name}.pipe")

def create_fifo(name):
    path = pipe_path(name)
    if not os.path.exists(path):
        os.mkfifo(path)

def load_config(path="config.toml"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} nicht gefunden.")
    with open(path, "r") as f:
        return toml.load(f)["DEFAULT"]
    



def test_config_laden():
    config = load_config("config.toml")
    assert config["handle"] == "Bileya"
    assert config["port"] == 5001
    assert config["imagepath"] == "images"
    assert config["autoreply"] == "Ich antworte später."


def write_to_fifo(name, message):
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
            if e.errno in (6, 32):  
                time.sleep(0.2)
            else:
                return
            
def read_from_fifo(name, blocking=True):
    path = pipe_path(name)
    flags = os.O_RDONLY
    if not blocking:
        flags |= os.O_NONBLOCK
    try:
        fd = os.open(path, flags)
        with os.fdopen(fd) as fifo:
            return fifo.readline().strip()
    except:
        return ""

