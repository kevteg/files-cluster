import socket
class uniObj():
    def __init__(self, socket, username = "", address = ""):
        self.username = username
        self.socket = socket
        self.address = address
        self.receiving = False

    def setUsername(self, username):
        self.username = username

    def getUsername(self):
        return self.username

    def setReceiving(self, receiving):
        self.receiving = receiving

    def getReceiving(self):
        return self.receiving

    def setAddress(self, address):
        self.address = address

    def getAddress(self):
        return str(self.address)

    def getSocket(self):
        return self.socket
