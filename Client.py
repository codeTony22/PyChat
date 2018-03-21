import socket

class Client:

    def __init__(self, clientSocket):
        self.clientSocket = clientSocket
        self.clientName = "anonymous"
        self.clientPassword = "@" #Empty password
        self.levels = "user"
        self.away = False
        self.status = False
        self.awayMessage = ""


    def send_message(self, message):
        self.clientSocket.sendall(message.encode('utf8'))

    def receive_message(self, size):
        return self.clientSocket.recv(size).decode('utf8').lower()

    def get_clientPassword(self):
        return self.clientPassword

    def set_clientPassword(self, clientPassword):
        self.clientPassword = clientPassword

    def get_clientName(self):
        return self.clientName

    def set_clientName(self, clientName):
        self.clientName = clientName

    def get_clientSocket(self):
        return self.clientSocket
    def set_socket(self, clientSocket):
        self.clientSocket = clientSocket

    def get_levels(self):
        return self.levels

    def set_levels(self, levels):
        self.levels = levels

    def set_banned(self, banned):
        self.banned = banned

    def get_banned(self):
        return self.banned

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status

    def get_away(self):
        return self.away

    def set_away(self, away):
        self.away = away

    def get_awayMessage(self):
        return self.awayMessage
    def set_awayMessage(self, awayMessage):
        self.awayMessage = awayMessage

