"""
Component Module

All Component data and methods is stored in these class instances
"""
import socket
import threading
from comp_mgr.config import NETWORK

class Component:

    def __init__(self, ip, system, type):
        self.ip = ip
        self.system = system
        self.type = type
        self.status = "Initializing..."
        self.display_name = self.type
        self.lock = threading.Lock()
        self.busy = False

        # Check, whether the component has a default IP
        if self.type in NETWORK["UNCONF"].keys():
            self.defaultip = NETWORK["UNCONF"][self.type]
        elif "Loadport" in self.type:
            self.defaultip = NETWORK["UNCONF"]["Rorze LP"]
    
    def establish_connection(self,port=12100):
        self.status = "Connecting..."
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        try:
            self.sock.connect((self.ip, port))
            # TODO [2:-3] cuts the b' and \\r that is always sent with a rorze status
            # what about other components?
            read = str(self.sock.recv(1024))[2:-3]

            # Store component type!
            self.type = read.split('.')[0]

            message = read.split('.')[1]

            if message == "CNCT":
                self.status = f"{self.type} is connected"

        except socket.timeout:
            self.status = "ERROR: Connection Timeout"
        except socket.error as e:
            self.status = f"Socket error: {e}"

    def send_and_read(self,command, buffer=1024):

        with self.lock:
            self.busy = True
            self.sock.sendall(command.encode('utf-8')) 
            read = str(self.sock.recv(buffer))[2:-3]
            # TODO Cut the Component name. Maybe include it again for non-rorze.
            message = read.split('.')[1]
            self.status = "Reading data..."
            # TODO Wait until information is read?
            try: 
                self.sock.settimeout(5)
                read = str(self.sock.recv(buffer))[2:-3]
                message = read.split('.')[1]
            except socket.timeout:
                self.status = "ERROR: Motion timeout"
            except socket.error as e:
                self.status = f"Socket error: {e}"
            finally:
                self.busy = False
        
        self.status = f"Output: {message}"

        return message
    
    def send_and_read_motion(self,command,buffer=1024):

        with self.lock:
            self.busy = True
            self.sock.sendall(command.encode('utf-8'))
            read = str(self.sock.recv(buffer))[2:-3]
            message = read.split('.')[1]
            self.status = "Component is in motion..."
            # Wait until motion finishes
            try: 
                self.sock.settimeout(120)
                read = str(self.sock.recv(buffer))[2:-3]
                message = read.split('.')[1]
            except socket.timeout:
                self.status = "ERROR: Motion timeout"
            except socket.error as e:
                self.status = f"Socket error: {e}"
            finally:
                self.busy = False
            
            self.status = f"Motion completed. {message}"

        return message

class Rorze(Component):

    def __init__(self, ip, system, type):
        self.ip = ip
        self.system = system
        self.type = type
        self.status = "Initializing..."
        self.display_name = f"Rorze {self.type}"
        self.lock = threading.Lock()
        self.busy = False

    def read_data(self):
        command = f"{self.type}.RTDT(0)"
        message = self.send_and_read(command, buffer=2**21) #2 MiB should suffice
        #self.status = message

    def origin_search(self, p1=0, p2=0):
        command = f"{self.type}.ORGN({p1},{p2})"
        message = self.send_and_read_motion(command)
        #self.status = f'Origin search completed. {message}'

class Sinfonia(Component):
    pass