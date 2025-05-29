import socket
import threading
from peer import Peer
#Test end to end Datei

def simulate_peer_connection(sender_peer, receiver_peer, message, result):
    """
    Simuliert eine Verbindung von einem Peer zu einem anderen und sendet eine Nachricht.
    Das Ergebnis wird im übergebenen result[] gespeichert.
    """

    # Simuliere ein lokales Verbindungs-Paar (wie TCP socket)....
    sock1, sock2 = socket.socketpair()

    def receiver():
        data = sock2.recv(1024).decode().strip()
        result.append(data)

    recv_thread = threading.Thread(target=receiver)
    recv_thread.start()

    msg = f"MSG {sender_peer.handle} {message}\n"
    sock1.sendall(msg.encode())

    recv_thread.join()
    sock1.close()
    sock2.close()

def test_end_to_end_message_exchange():
    alice = Peer("Alice", "127.0.0.1", 5001)
    bob = Peer("Bob", "127.0.0.1", 5002)

    result = []
    simulate_peer_connection(alice, bob, "Hallo Bob!", result)

    assert len(result) == 1
    assert result[0].startswith("MSG Alice Hallo Bob!")