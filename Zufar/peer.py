class Peer:
    def __init__(self, handle, ip, port):
        self.handle = handle
        self.ip = ip
        self.port = port

    def get_address(self):
        return (self.ip, self.port)
