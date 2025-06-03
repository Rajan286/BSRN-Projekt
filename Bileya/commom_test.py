import os 
import toml

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