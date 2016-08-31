import socket
class uniObj():
    def __init__(self, socket, username = None, address = None):
        self.username = username
        self.socket = socket
        self.address = address

    def setUsername(self, username):
        self.username = username

    def getUsername(self):
        return self.username

    def setAddress(self, address):
        self.address = address

    def getAddress(self):
        return self.address

    def getSocket(self):
        return self.socket
