import socket

class DiscoveryService:
    def __init__(self, users, port=5000):
        self.users = users
        self.port = port

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self.port))
        print(f"[Discovery] Lausche auf UDP-Port {self.port}")

        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode().strip()
            print(f"[Discovery] Nachricht '{message}' von {addr} erhalten")

            if message.startswith("whois"):
                # Wir teilen die Nachricht in zwei Teile auf: "whois" und der Benutzername
                teile = message.split(" ", 1)
                if len(teile) == 2:
                    gesuchter_name = teile[1].strip()
                    # Wir suchen den Benutzer mit diesem Namen
                    gefunden = False
                    for user in self.users:
                        if user.handle == gesuchter_name:
                            antwort = f"iam {user.handle} {user.ip} {user.port}"
                            sock.sendto(antwort.encode(), addr)
                            print(f"[Discovery] Antwort '{antwort}' an {addr} geschickt")
                            gefunden = True
                            break
                    if not gefunden:
                        print(f"[Discovery] Kein Benutzer mit Namen '{gesuchter_name}' gefunden.")
                else:
                    print("[Discovery] Falsches Format für whois-Anfrage.")