class User:
    def __init__(self, handle, ip, port):
        self.handle = handle  
        self.ip = ip          
        self.port = port      

    def toString(self):
        return f"User(handle='{self.handle}', ip='{self.ip}', port={self.port})"