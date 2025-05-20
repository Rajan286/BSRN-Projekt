from peer import Peer

def test_peer_get_address():
    p = Peer("Alice", "127.0.0.1", 5000)
    assert p.get_address() == ("127.0.0.1", 5000)
    assert p.handle == "Alice"
