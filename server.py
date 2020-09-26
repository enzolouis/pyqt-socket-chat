import yaml
import threading
import socket

# commentaire à refaire en anglais.

class ServerIO(socket.socket):

    def __init__(self, *args, **kwargs):
        socket.socket.__init__(self, *args, **kwargs)

        with open("config.yaml", "r") as file:
            config = yaml.load(file, Loader=yaml.Loader)

        PORT = config["PORT"]
        self.BUFSIZ = config["BUFSIZ"]

        self.clients = {}
        self.commands = ["/quit", "/color"]
        self.no_commands = [("\\"+command) for command in self.commands]

        # self.server_sock = socket.socket()

        self.bind(("", PORT))
        self.listen(5)

    def accept_(self): # collisions -> socket.socket.accept
        print("ACCEPT INCOMING")
        """Gère l'arrivée du client, puis le mène vers le tchat"""
        while True:
            print("ACCEPT => .")
            try:
                client, client_address = self.accept()
                
                print(f"+1 client -> {client_address}")
                client.send(f"{'Room is empty' if not self.clients else f'Room has {len(self.clients)} player'} ! Type your name and press enter to join !".encode("utf8"))

                self.send_all_client("A player is on the lobby")

                threading.Thread(target=self.manage_client_protocol, args=(client, client_address)).start()
            except Exception as e:
                print(e, type(e))

    def manage_client_protocol(self, client, address):
        """Gère le parcours du client, de l'inscription à son départ"""


        name = client.recv(self.BUFSIZ).decode("utf8")


        client.send(f"{name} ! Welcome !".encode("utf-8"))

        # + 1 parce que il y a + 1 nouveau joueurs. Et qu'on l'ajoute à la ligne après, on aurait pu mettre la ligne avant, mais le send_all_client
        # aurait envoyé "has joined the chat" au nouveau joueur
        self.send_all_client(f"--> {name} has joined the chat ! We are now {len(self.clients) + 1}")

        self.clients[client] = name

        self.send_all_client(f"<YOTfb3po7lBNv19in6yC> / {len(self.clients)}")
        while True:
            try:
                msg = client.recv(self.BUFSIZ).decode("utf8")

                print("server receive")

                if msg in self.no_commands:
                    self.send_all_client(f"/{msg[2:]}", name+": ")

                elif msg == self.commands[0]:
                    client.close()
                    self.clients.pop(client)
                    self.send_all_client(f"{name} has left the chat.")
                    self.send_all_client(f"<YOTfb3po7lBNv19in6yC> / {len(self.clients)}")
                    print(f"-1 client -> {address}")
                    break
                else:
                    self.send_all_client(msg, name+": ")
            except OSError:
                break
                

    def send_all_client(self, msg, member=""):
        """Envoyer l'informations à chaque client"""
        for sock in self.clients:
            sock.send((member+msg).encode("utf-8"))



if __name__ == "__main__":
    
    server = ServerIO(socket.AF_INET, socket.SOCK_STREAM)

    print(f"Server on. {'-'*50}")
    server.accept_() # bloquant jusqu'à fermeture du serveur

    server.close() # socket.socket.close