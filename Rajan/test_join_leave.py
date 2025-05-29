def test_join_parsing():
    msg = "JOIN Alice 5010\n"
    parts = msg.strip().split()
    assert parts[0] == "JOIN"
    assert parts[1] == "Alice"
    assert int(parts[2]) == 5010

def test_leave_parsing():
    msg = "LEAVE Bob\n"
    parts = msg.strip().split()
    assert parts[0] == "LEAVE"
    assert parts[1] == "Bob"
