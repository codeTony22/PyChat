import Serialization as Manipulate_users
from Client import Client


class Users:

    def __init__(self):
        self.list_of_clients = []  # List of Client

    def get_list_of_clients(self):
        return self.list_of_clients

    def create_client(self, clientSocket , clientName, clientPassword):
        return Manipulate_users.authorize_client(clientName , clientPassword)

    def append_client(self, socketClient, client):
        pass
    def delete_client(self, client):
        self.list_of_clients.remove(client)

    def find_client(self, client):
        # gotta read the file and compare
        pass

    def validate_client(self, client):
        # use find_client to validate the user
        pass