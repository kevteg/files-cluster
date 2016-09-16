import socket
class uniObj():
    def __init__(self, socket = None, username = "", address = ""):
        self.username = username
        self.socket = socket
        self.address = address
        self.receiving = False
        self.file_list = []
        self.not_ask_for = []

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

    def setFileList(self, new_list):
        new_list = [element[0] for element in new_list]
        if new_list != self.file_list:
            self.not_ask_for = self.not_ask_for + list(set(self.file_list) - set(new_list))
            self.file_list = new_list

    def getNotAskFor(self):
        return self.not_ask_for
