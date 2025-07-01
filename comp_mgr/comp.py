"""
Component Module

All Component data and methods is stored in these class instances
"""
import socket
from comp_mgr.config import NETWORK

class Component:
    def __init__(self, ip, system, type):
        self.ip = ip
        self.system = system
        self.type = type
        self.status = "Initializing..."

        # Check, whether the component has a default IP
        if self.type in NETWORK["UNCONF"].keys():
            self.defaultip = NETWORK["UNCONF"][self.type]
        elif "Loadport" in self.type:
            self.defaultip = NETWORK["UNCONF"]["Rorze LP"]
    
    def establish_connection(self,port=12100):
        self.status = "Connecting..."

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect((self.ip, port))
            # Show response
            read = str(sock.recv(1024))[2:-3]
            self.type = read.split('.')[0]
            message = read.split('.')[1]

            if message == "CNCT":
                self.status = f"{self.type} is connected"

        except socket.timeout:
            self.status = "ERROR: Connection Timeout"
        except socket.error as e:
            self.status = f"Socket error: {e}"

        # UNTESTED METHOD
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        #     sock.settimeout(5)
        #     sock.connect((self.ip,port))

class Rorze_LP(Component):
    pass

class Rorze_PA(Component):
    pass

class Rorze_RO(Component):
    pass

class Sinfonia_LP(Component):
    pass