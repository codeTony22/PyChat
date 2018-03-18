import socket
import sys
import threading
import Channel
from Client import Client
from Serialization import Serialization


class Server:
    SERVER_CONFIG = {"MAX_CONNECTIONS": 15}

    HELP_MESSAGE = """\n> The list of commands available are:

/help                   - Show the instructions
/join [channel_name]    - To create or switch to a channel.
/quit                   - Exits the program.
/list                   - Lists all available channels.\n\n""".encode('utf8')

    def __init__(self, host=socket.gethostbyname('localhost'), port=50000, allowReuseAddress=True):
        self.address = (host, port)
        self.channels = {} # Channel Name -> Channel
        self.serializer = Serialization()
        self.channels_client_map = {} # Client Name -> Channel Name
        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as errorMessage:
            sys.stderr.write("Failed to initialize the server. Error - %s\n", str(errorMessage))
            raise

        if allowReuseAddress:
            self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.serverSocket.bind(self.address)
        except socket.error as errorMessage:
            sys.stderr.write('Failed to bind to ' + self.address + '. Error - %s\n', str(errorMessage))
            raise

    def listen_thread(self, defaultGreeting="\n> Welcome to our chat app!!! What is your name?\n"):
        while True:
            print("Waiting for a client to establish a connection\n")
            #Accept connection, returns tuple
            clientSocket, clientAddress = self.serverSocket.accept()

            client = Client(clientSocket)

            # Authorize user
            client = self.serializer.authorize_client(client)

            # client was returned with None
            while client is None:
                # Repeat until the is an authenticated or new client
                client = self.serializer.authorize_client(client)

            print(client.get_clientName())
            print(client.get_clientPassword())
            print(client.get_levels())
            print(str(client.get_status()))

            #Stablish connection
            print("Connection established with IP address {0} and port {1}\n".format(clientAddress[0], clientAddress[1]))

            clientThread = threading.Thread(target=self.client_thread, args=(client,))
            clientThread.start()

    def start_listening(self):
        self.serverSocket.listen(Server.SERVER_CONFIG["MAX_CONNECTIONS"])
        listenerThread = threading.Thread(target=self.listen_thread)
        listenerThread.start()
        listenerThread.join()

    def client_thread(self, client, size=4096):

        welcomeMessage = '> Welcome %s, type /help for a list of helpful commands.\n\n' % client.get_clientName()
        client.send_message(welcomeMessage)

        while True:
            chatMessage = client.receive_message(size)

            if not chatMessage:
                break

            if '/quit' in chatMessage:
                self.quit(client.get_socket(), client.get_clientName())
                break
            elif '/list' in chatMessage:
                self.list_all_channels(client.get_clientSocket())
            elif '/help' in chatMessage:
                self.help(client.get_clientSocket())
            elif '/join' in chatMessage:
                self.join(client.get_clientSocket(), chatMessage, client.get_clientName())
            else:
                self.send_message(client.get_clientSocket(), chatMessage + '\n' , client.get_clientName())
        client.get_socket().close()

    def privmsg(self, chatMessage):
        commands = chatMessage.split()
        msgtarget = commands[1]


    def kick(self, clientName, chatMessage):
        list_of_commands = chatMessage.split()
        channel = list_of_commands[1]
        clientToRemove = list_of_commands[2]
        message = list_of_commands[3]

        #This command can be issued by any user
        if clientToRemove in self.channels_client_map:
            del self.channels_client_map[clientToRemove]
        #TO DO - send message to the user


    def kill(self, clientSocket , clientName, chatMessage):
        list_of_commands = chatMessage.split()
        if clientName in self.channels_client_map:
            del self.channels_client_map[clientName]
        #TO DO SEND NAME


    def ison(self, chatMessage):
        nicknames = chatMessage[6:]
        nicknames_list = nicknames.split()

        query = []

        for name in nicknames_list:
            if name in self.channels_client_map:
                query.append(name)


    """
    Information of the server. Program only uses one 
    server. Add information about the server. 
    """
    def info(self, clientSocket):
        clientSocket.sendall("The Server version is 1.0.")

    def away(self, clientSocket, chatMessage):
        PRIVMSG = chatMessage[5:]
        if PRIVMSG:
            self.away_clients[clientSocket] = chatMessage

    #Kill the server, any user can
    #TO DO - FIX
    def die(self, clientSocket):
        self.server_shutdown()

    def quit(self, clientSocket, clientName):
        clientSocket.sendall('/quit'.encode('utf8'))
        self.remove_client(clientName)

    def list_all_channels(self, clientSocket):
        if len(self.channels) == 0:
            chatMessage = "\n> No rooms available. Create your own by typing /join [channel_name]\n"
            clientSocket.sendall(chatMessage.encode('utf8'))
        else:
            chatMessage = '\n\n> Current channels available are: \n'
            for channel in self.channels:
                chatMessage += "    \n" + channel + ": " + str(len(self.channels[channel].clients)) + " user(s)"
            chatMessage += "\n"
            clientSocket.sendall(chatMessage.encode('utf8'))

    def help(self, socket):
        socket.sendall(Server.HELP_MESSAGE)


    def join(self, clientSocket, chatMessage, clientName):
        isInSameRoom = False

        if len(chatMessage.split()) >= 2:
            channelName = chatMessage.split()[1]

            if clientName in self.channels_client_map: # Here we are switching to a new channel.
                if self.channels_client_map[clientName] == channelName:
                    clientSocket.sendall(("\n> You are already in channel: " + channelName).encode('utf8'))
                    isInSameRoom = True
                else: # switch to a new channel
                    oldChannelName = self.channels_client_map[clientName]
                    self.channels[oldChannelName].remove_client_from_channel(clientName) # remove them from the previous channel

            if not isInSameRoom:
                if not channelName in self.channels:
                    newChannel = Channel.Channel(channelName)
                    self.channels[channelName] = newChannel

                self.channels[channelName].clients[clientName] = clientSocket
                self.channels[channelName].welcome_client(clientName)
                self.channels_client_map[clientName] = channelName
        else:
            self.help(clientSocket)

    def send_message(self, clientSocket, chatMessage, clientName):
        if clientName in self.channels_client_map:
            self.channels[self.channels_client_map[clientName]].broadcast_message(chatMessage, clientName + ": ")
        else:
            chatMessage = """\n> You are currently not in any channels:

Use /list to see a list of available channels.
Use /join [channel name] to join a channels.\n\n""".encode('utf8')

            clientSocket.sendall(chatMessage)


    def remove_client(self, clientName):
        if clientName in self.channels_client_map:
            self.channels[self.channels_client_map[clientName]].remove_client_from_channel(clientName)
            del self.channels_client_map[clientName]
        print("Client: " + clientName + " has left\n")

    def server_shutdown(self):
        print("Shutting down chat server.\n")
        self.serverSocket.shutdown(socket.SHUT_RDWR)
        self.serverSocket.close()

def main():
    chatServer = Server()

    print("\nListening on port " + str(chatServer.address[1]))
    print("Waiting for connections...\n")

    chatServer.start_listening()
    chatServer.server_shutdown()

if __name__ == "__main__":
    main()
