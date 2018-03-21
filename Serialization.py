from Client import Client
import socket
import json


class Serialization:

    def read_ServerConfigInfo(self, clientSocket):
        with open("chatserver.conf", "r", encoding="utf-8") as serverFile:
            size_to_read = 100
            f_contents = serverFile.readline(size_to_read)

            while len(f_contents) > 0:
                line = f_contents
                clientSocket.sendall(line.encode("utf-8"))
                f_contents = serverFile.readline(size_to_read)

    def reading_user_txt_file(self):
        list_clients = []

        # open the file and read the contents
        file = open("users.txt", "r", encoding="utf-8")
        size_to_read = 100
        if file.mode == "r":
            # use the read() function to read the content
            f_contents = file.readline(size_to_read)
            # The user.txt is formatted in the following way
            # user password admin true/false
            while len(f_contents) > 0:
                line = f_contents.split()
                client = Client(line[0], line[1], line[2] , line[3])
                list_clients.append(client)
                f_contents = file.readline(size_to_read)

        file.close()

        return list_clients

    def reading_users_json_file(self):
        list_of_users = []

        with open("user.json", "r") as file:
            data = json.load(file)

        for person in data['username']:
            list_of_users.append(person)
        print(type(data['username']))


    '''
        Find the user in the json file, return the client.
    '''
    def authorize_client(self, client):
        size = 4096
        with open("user.json", "r", encoding='utf-8') as json_file:
            #load json file
            json_users = json.load(json_file)

            # Send welcome message, and ask for username
            welcomeMessage = "\n> Welcome to our chat app!!!\n Create or enter your username:\n"
            client.send_message(welcomeMessage)
            username = client.receive_message(size)

            #Ask for password
            passwordMessage = "\n> Enter password: \n"
            client.send_message(passwordMessage)
            password = client.receive_message(size)

            # Find the user on json file
            for user in json_users:
                #is the user in the user.json file?
                if user['username'] == username:
                    #validate password
                    if user['password'] == password:

                        client.set_clientName(username)
                        client.set_clientPassword(password)
                        client.set_levels(user['levels'])
                        client.set_status(user['status'])
                        return client
                    else:
                        # Ask the user to repeat his password
                        repeatPasswordMessage = "\n> Passwords did not match. Access denied. Please enter your password one more time. \n"
                        client.send_message(repeatPasswordMessage)
                        repeated_password = client.receive_message(size)
                        if repeated_password == user['password']:
                            client.set_clientName(username)
                            client.set_clientPassword(password)
                            client.set_levels(user['levels'])
                            client.set_status(user['status'])
                            return client
                        else:
                            return None

        #Register new user. Not such username was found in the json db.
        with open("user.json", mode="w", encoding='utf-8') as json_file:
            registeringMessage = "\n> Register the new user. Your username and password are registered.\n"
            client.send_message(registeringMessage)
            #set up client object with username and password
            client.set_clientName(username)
            client.set_clientPassword(password)
            '''
            # unpack client and serialize
            # Register client in the db
            print(type(json_users))
            json_users.append(data_client)
            '''
            data_client = {
                'username': client.get_clientName(),
                'password': client.get_clientPassword(),
                'levels': client.get_levels(),
                'status': client.get_status()
            }

            json_users.append(data_client)
            json_file.write(json.dumps(json_users, indent=4))
            # Close file and return the new client
            json_file.close()
            return client

    def append_user_to_txt_file(self, user):
        with open("users.txt" , "a+" , encoding="utf-8") as file:
            file.write(user.username + " " + user.password + " " + user.levels + " " + user.status )

    def write_json_file(self, user):
        data = {
            "username": user.username,
            "password": user.password,
            "levels": user.levels,
            "status": user.status
        }

        with open("user.json", "w") as file:
            json.dump(data, file)


if __name__ == "__main__":
    ser = Serialization()




