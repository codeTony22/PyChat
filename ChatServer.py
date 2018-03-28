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
                self.join(chatMessage, client)
            elif '/away' in chatMessage:
                self.away(client, chatMessage)
            elif '/info' in chatMessage:
                self.info(client.get_clientSocket())
            elif '/ison' in chatMessage:
                query = self.ison(chatMessage)
                if query == []:
                    client.send_message("\n>None of the nickname/s are connected in the network\n")
                else:
                    for name in query:
                        client.send_message("\n>" + name + " is connected.\n")
            elif '/kick' in chatMessage:
                self.kick(client, chatMessage)
            elif '/kill' in chatMessage:
                self.kill(client, chatMessage)
            elif '/privmsg' in chatMessage:
                self.privmsg(client, chatMessage)
            elif '/invite'  in chatMessage:
                self.invite(client, chatMessage)
            elif '/mode' in chatMessage:
                self.mode(client, chatMessage)
            elif '/nick' in chatMessage:
                self.nick()
            else:
                self.send_message(client.get_clientSocket(), chatMessage + '\n' , client.get_clientName())
        client.get_socket().close()

    def privmsg(self, client, chatMessage):
        args_list = chatMessage.split()
        msg_target = args_list[1]
        message = args_list[2]

        self.channels[self.channels_client_map[msg_target]].broadcast_message(message, msg_target)

    def mode(self, client , chatMessage):
        args_list = chatMessage.split()

        if  len(args_list) >= 3:
            flag = args_list[2]
            #mode change user flag -u must be set
            if flag == "-u":
                pass
            elif flag == "-c":
                pass

    def get_all_channelName(self):
        result = []
        for channel in self.channels:
            result.append(channel)

        return result

    def invite(self, client, chatMessage):
        arg_list = chatMessage.split()

        if len(arg_list) >= 2:
            msgtarget = arg_list[1]
            channel = arg_list[2]
            if channel in self.channels:
                if channel.get_mode() == True:
                    if client.get_levels() == "channelop" or client.get_levels() == "admin":
                        self.join(msgtarget)
                    else:
                        client.send_message("\n>Invite Incomplete. Not a channel operator.\n")
                else:
                    if client.get_clientName() in self.channels_client_map:
                        target_client = self.find_client_target(msgtarget)
                        target_client.send_message("\n>" + client.get_clientName() + " has invited you to a channel. Leaving your channel.\n")
                        self.join(target_client)

            else:
                target_client_object = self.find_client_target(msgtarget)
                self.join_invite(target_client_object, channel)
                self.join_invite(client, channel)
        else:
            client.send_message("\n>Command Usage Error.\n\n>/invite msg_target channel \n")


    def join_invite(self, client, channelName):
        isInSameRoom = False

        if client.get_clientName() in self.channels_client_map:
            if channelName in self.channels_client_map[client.client.get_clientName()]:
                # User already on that channel
                client.send_message("\n> You are already in channel: " + channelName)
                isInSameRoom = True
            elif not channelName in self.channels_client_map[client.client.get_clientName()] and channelName in self.channels:
                self.channels[channelName].clients[client.get_clientName()] = client
                self.channels_client_map[client.get_clientName()].append(channelName)

        if not isInSameRoom:
            if not channelName in self.channels:
                newChannel = Channel.Channel(channelName)
                self.channels[channelName] = newChannel
            self.channels[channelName].clients[client.get_clientName()] = client
            self.channels[channelName].welcome_client(client.get_clientName())
            self.channels_client_map[client.get_clientName()].append(channelName)

    '''
    Find_client_target is a function that find the msgtarget if the user is connected. 
    If given the clientName. returns None if client was not found.
    '''
    def find_client_target(self, msgtarget):
        if msgtarget in self.channels_client_map:
            return self.channels[self.channels_client_map[msgtarget]]
        return None



    def kick(self, client , chatMessage):
        if client.get_levels() == "channelop" or client.get_levels() == "admin":
            args = chatMessage[5:]
            list_args = args.split()

            channelName = list_args[0]
            clientName = list_args[1]
            message = list_args[2]
            if clientName in self.channels[channelName].clients:
                del self.channels[channelName].clients[clientName]
                client.send_message(message)

    def kill(self, client , chatMessage):
        if client.get_levels() == "channelop" or client.get_levels() == "admin":
            args_list = chatMessage.split()
            clientName = args_list[1]
            message = args_list[2]

            if clientName in self.channels_client_map:
                self.channels[self.channels_client_map[clientName]].clients[clientName].send_message(message)
                del self.channels[self.channels_client_map[clientName]].clients[clientName]
                del self.channels_client_map[clientName]


    def ison(self, chatMessage):
        nicknames = chatMessage[6:]
        nicknames_list = nicknames.split()

        query = []

        for name in nicknames_list:
            if name in self.channels_client_map:
                query.append(name)

        return query

    """
    Information of the server. Program only uses one 
    server. Add information about the server. 
    """
    def info(self, clientSocket):
        self.serializer.read_ServerConfigInfo(clientSocket)


    def away(self, client, chatMessage):
        PRIVAWAAYMSG = chatMessage[5:]

        if PRIVAWAAYMSG is "":
            client.set_away(False)

        if client.get_away() == False and PRIVAWAAYMSG:
            client.set_away(True)
            client.set_awayMessage(PRIVAWAAYMSG)


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


    def join(self, chatMessage, client):
        isInSameRoom = False

        if len(chatMessage.split()) >= 2:
            channelName = chatMessage.split()[1]

            if client.get_clientName() in self.channels_client_map:
                if channelName in self.channels_client_map[client.client.get_clientName()]:
                    # User already on that channel
                    client.send_message("\n> You are already in channel: " + channelName)
                    isInSameRoom = True
                elif not channelName in self.channels_client_map[
                    client.client.get_clientName()] and channelName in self.channels:
                    self.channels[channelName].clients[client.get_clientName()] = client
                    self.channels_client_map[client.get_clientName()].append(channelName)

            if not isInSameRoom:
                if not channelName in self.channels:
                    newChannel = Channel.Channel(channelName)
                    self.channels[channelName] = newChannel
                self.channels[channelName].clients[client.get_clientName()] = client
                self.channels[channelName].welcome_client(client.get_clientName())
                self.channels_client_map[client.get_clientName()].append(channelName)
        else:
            self.help(client.get_clientSocket())

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
