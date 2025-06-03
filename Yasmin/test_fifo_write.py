import threading
from Yasmin.common_test import create_fifo, write_to_fifo, read_from_fifo, pipe_path

def test_fifo_write_read(tmp_path):
    import Yasmin.common_test as common_test
    common_test.PIPE_DIR = str(tmp_path)

    name = "User_fifo"
    create_fifo(name)

    result = []

    def reader():
        msg = read_from_fifo(name)
        result.append(msg)

    t = threading.Thread(target=reader)
    t.start()

    write_to_fifo(name, "Hallo User!")
    t.join(timeout=2)

    assert result and result[0] == "Hallo User!"
