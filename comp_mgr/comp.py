"""
Component Module

All Component data and methods is stored in these class instances
"""
import logging
import json
import socket
import threading
import time
from comp_mgr.config import NETWORK

logger = logging.getLogger(__name__)

class Component:

    def __init__(self, ip, system, type):
        self.ip = ip
        # System (e.g. example 'WMC')
        self.system = system
        # Component type (e.g. 'Robot')
        self.type = type
        # Display name for CLI (e.g. 'Robot')
        self.display_name = type

        self.status = "Initializing..."
        logger.info(f"Initializing {self.display_name}...")
        self.lock = threading.Lock()
        self.busy = False
    
    def establish_connection(self,port=12100,retries=1):
        self.status = "Connecting..."
        logger.info(f"Connecting to {self.display_name}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)

        for i in range(retries+1):

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
                    logger.info(f"Connection to {self.display_name} successful")
                    break

            except socket.timeout:
                self.status = "ERROR: Connection Timeout"
                logger.error(f"Connection Timeout")
                self.busy = True
            except socket.error as e:
                self.busy = True
                if i == 0:
                    logger.warning(f"Connection attempt unsuccessful... Retrying {retries} more time")
                    time.sleep(1)
                else:
                    self.status = f"Socket error: {e}"
                    logger.error(f"Socket error: {e}")
            # finally:
            #     self.busy = False

    def send_and_read(self, command: str, buffer: int=1024) -> str:

        with self.lock:
            self.busy = True
            self.sock.sendall(command.encode('utf-8')) 
            logger.debug(f"Sending: {command}")
            read = str(self.sock.recv(buffer))[2:-3]
            # TODO raise Exception when Acknowledge fails - such that the program doesn't crash
            # TODO Cut the Component name. Maybe include it again for non-rorze.
            message = read.split('.')[1]
            self.status = "Reading data..."
            logger.debug(f"Reading data... {message}")
            try: 
                self.sock.settimeout(5)
                read = str(self.sock.recv(buffer))[2:-3]
                message = read.split('.')[1]
            except socket.timeout:
                self.status = "ERROR: Motion timeout"
                logger.error(f"Motion timeout")
            except socket.error as e:
                self.status = f"Socket error: {e}"
                logger.error(f"Socket error: {e}")
            finally:
                self.busy = False
        
        self.status = f"Output: {message}"
        logger.info(f"Response from {self.display_name}: - {message}")

        return message
    
    def send_and_read_motion(self,command,buffer=1024):

        with self.lock: # TODO THIS SHOULD NOT BLOCKING -- EMO NEEDS TO BE POSSIBLE
            self.busy = True
            self.sock.sendall(command.encode('utf-8'))
            logger.debug(f"Sending: {command}")
            read = str(self.sock.recv(buffer))[2:-3]
            message = read.split('.')[1]
            self.status = "Component is in motion..."
            logger.debug(f"Component is in motion... {message}")
            # Wait until motion finishes
            try: 
                self.sock.settimeout(120)
                read = str(self.sock.recv(buffer))[2:-3]
                message = read.split('.')[1]
            except socket.timeout:
                self.status = "ERROR: Motion timeout"
                logger.error(f"Motion timeout")
            except socket.error as e:
                self.status = f"Socket error: {e}"
                logger.error(f"Socket error: {e}")
            finally:
                self.busy = False
            
            self.status = f"Motion completed. {message}"
            logger.info(f"Motion completed. {message}")

        return message

class Rorze(Component):

    def __init__(self, ip, system, type):
        self.ip = ip
        # System (e.g. example 'WMC')
        self.system = system
        # Component type (e.g. 'eTRB0')
        self.type = type
        # Display name for CLI (e.g. 'Rorze eTRB0')
        self.display_name = f"Rorze {type}"
        # Name of the component in Rorze terms (e.g. 'TRB0')
        self.name = self.read_name(type)

        self.status = "Initializing..."
        logger.info(f"Initializing {self.display_name}...")
        self.lock = threading.Lock()
        self.busy = False
    
    def read_name(self, type: str):
        """
        Rorze components will have a prefix that contain type information.
        This prefix has to have a character removed, such that commands can be sent.
        Example: extended_type="eTRB0" -> type="TRB0"
        """
        if type == "SIMULATIONeTRB0":
            name = type
        else:
            name = "o"+type[-4:]
        return name

    def origin_search(self, p1: int=0, p2: int=0):
        command = f"{self.name}.ORGN({p1},{p2})"
        message = self.send_and_read_motion(command)
        self.status = f"Origin search completed: {message}"

    def get_rotary_switch_value(self):
        command = f"{self.name}.GTDT(3)"
        message = self.send_and_read(command)  
        self.status = f"Rotary switch position: {message}"

    def acquire_system_data(self):
        """
        This serves the same purpose as the 'Read Data' button in the
        Rorze maintenance software. It is slightly different for each component.
        """
        # Save data to a dictionary
        system_data = {}

        # Loadport Backup
        if ("STG" in self.type) or ("SIMULATION" in self.type):
            data_fields = [
                "DEQU",
                "DRES",
                "DRCI",
                "DRCS",
                "DMNT",
                "YAX1",
                "ZAX1",
                "DSTG",
                "DMPR",
                "DPRM",
                "DCST",
                "DE84"
                ]
        else:
            raise Exception(f"Data acquisition not implemented for {self.type}")
            
        # Get Own IP address
        command = f"{self.name}.GTDT[1]"
        system_data["STDT[1]"] = self.send_and_read(command)

        # Get remaining system data
        for field in data_fields:
            command = f"{self.name}.{field}.GTDT"
            system_data[field] = self.send_and_read(command, buffer=2**21) # 2MiB should always suffice

        with open('testing/System_data.json', 'w') as out:
            json.dump(system_data, out, indent=4)

class Sinfonia(Component):
    pass