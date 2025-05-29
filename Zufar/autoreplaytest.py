# Konfiguration laden
import toml
from peer import Peer

# Bsp Peer-Liste
peers = {
    "Bob": Peer("Bob", "127.0.0.1", 5001)
}

# Konfiguration laden
try:
    full_config = toml.load("config.toml")  # Ganze Datei laden
    config = full_config.get("DEFAULT", {})  # DEFAULT-Wert setzen
    if config:
        print(" Konfiguration erfolgreich")
    else:
        print(" 'DEFAULT'-Block in config.toml ist leer oder fehlt.")
except Exception as e:
    print(f" Anderer Fehler beim Laden der Konfiguration: {e}")
    config = {}






#  Simulierte Sucket Kommunikationn
def send_msg(target, text):
    peer = peers.get(target)
    if not peer:
        print(f" Peer '{target}' nicht gefunden.")
        return
    print(f" [Simuliert] Nachricht an {target} gesendet: {text}")

#  Simuliere emfpangene  Nachricht und test AutoReply
def receive_message_simulated(sender, message_text):
    print(f"[{sender}] {message_text}")
    auto = config.get("autoreply", "").strip()
    if auto and "[AutoReply]" not in message_text and sender != config["handle"]:
        send_msg(sender, f"[AutoReply] {auto}")
        print(" AutoReply wurde ausgelöst.")
    else:
        print(" Keine AutoReply-Bedingung erfüllt.")

#  Test starten
if __name__ == "__main__":
    print(" Starte AutoReply-Test...")
    receive_message_simulated("Bob", "Hey Alice, bist du da?")
