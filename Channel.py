
class Channel:
    def __init__(self, name):
        self.clients = {} # Client Name -> client
        self.channel_name = name
        self.topic = "General"
        self.channe_op = []


    def welcome_client(self, clientName=""):
        for name, client in self.clients.items():
            if name is clientName:
                chatMessage = '\n\n> {0} have joined the channel {1}!\n'.format("You", self.channel_name)
                client.send_message(chatMessage)
            else:
                chatMessage = '\n\n> {0} has joined the channel {1}!\n'.format(clientName, self.channel_name)
                client.send_message(chatMessage)

    def broadcast_message(self, chatMessage, clientName=''):
        for name, client in self.clients.items():
            if name is clientName:
                client.send_message(("You: " + chatMessage))
            else:
                client.send_message(clientName + chatMessage)

    def remove_client_from_channel(self, clientName):
        del self.clients[clientName]
        leave_message = "\n" + clientName + " has left the channel " + self.channel_name + "\n"
        self.broadcast_message(leave_message)
