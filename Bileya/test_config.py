import toml
import os

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