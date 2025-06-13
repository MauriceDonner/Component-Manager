"""
Component Module

All Component data and methods is stored in these class instances
"""
import socket
from comp_mgr.config import NETWORK

class Component:
    def __init__(self, name, system, type):
        self.name = name
        self.ip = NETWORK[system][type]
        self.system = system
        self.type = type

        # Check, whether the component has a default IP
        if self.type in NETWORK["UNCONF"].keys():
            self.defaultip = NETWORK["UNCONF"][self.type]
        elif "Loadport" in self.type:
            self.defaultip = NETWORK["UNCONF"]["Rorze LP"]
    
    def establish_connection(self,ip,port=12100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((ip,port))
