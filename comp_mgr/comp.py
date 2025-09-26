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
from typing import TextIO, Union

logger = logging.getLogger(__name__)

class Component:

    def __init__(self, comp_info: dict):
        self.ip = comp_info["IP"]
        # System (e.g. example 'WMC')
        self.system = comp_info["System"]
        # Component type (e.g. 'Robot')
        self.type = comp_info["Type"]
        # Display name for CLI (e.g. 'Robot')
        self.display_name = comp_info["Name"]

        self.status = "Initializing..."
        logger.info(f"Initializing {self.display_name}...")
        self.lock = threading.Lock()
        self.busy = False
    
    def establish_connection(self, port=12100, retries=1, timeout=3):
        """
        General attempt to establish connection to a component.
        This method might never be used since the different components have their own class
        """

        self.status = "Connecting..."
        logger.info(f"Connecting to {self.display_name}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)

        for i in range(retries+1):

            try:
                self.sock.connect((self.ip, port))
                read = str(self.sock.recv(1024))
                logger.debug(f"Recieved: {read}")

                if read:
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
    
    def recv_until_newline(self, timeout=0.1):
        self.sock.settimeout(timeout)
        data = b""
        while True:
            chunk = self.sock.recv(1024)
            if not chunk:
                break  # connection closed
            data += chunk
            if (b"\r" in chunk):
                logger.debug('Escape sequence found')
                break
        return data.decode('utf-8').strip()

    def send_and_read(self, command: str, buffer: int=1024) -> str:

        # Add a \r at the end of a command!
        command = f"{command}\r"

        with self.lock:
            self.busy = True
            logger.debug(f"Sending: {command}")
            self.sock.sendall(command.encode('utf-8')) 
            self.status = "Reading data..."
            try: 
                read = self.recv_until_newline()
                logger.debug(f"Receive: {read}")
                # TODO Cut the Component name. Maybe include it again for non-rorze.
                message = read #.split('.')[1]
                # Simulation always treats it like motion command
                if "SIMULATION" in self.type:
                    read = self.sock.recv(1024)
                    logger.debug(f"Receive: {read}")
                    message = read 
            except socket.timeout:
                self.status = "ERROR: Timeout"
                logger.error(f"Timeout")
            except socket.error as e:
                self.status = f"Socket error: {e}"
                logger.error(f"Socket error: {e}")
            finally:
                self.busy = False
        
        self.status = f"Output: {message}"

        return message
    
    def send_and_read_motion(self,command,buffer=1024):
        
        with self.lock: # TODO THIS SHOULD NOT BLOCKING -- EMO NEEDS TO BE POSSIBLE
            self.busy = True
            self.sock.sendall(command.encode('utf-8'))
            logger.debug(f"Sending: {command}")
            read = str(self.sock.recv(buffer))[2:-3]
            message = read #.split('.')[1]
            self.status = "Component is in motion..."
            logger.debug(f"Component is in motion... {message}")
            # Wait until motion finishes
            try: 
                self.sock.settimeout(120)
                read = str(self.sock.recv(buffer))[2:-3]
                message = read #.split('.')[1]
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

    def __init__(self, comp_info: dict):
        self.ip = comp_info["IP"]
        # System (e.g. example 'WMC')
        self.system = comp_info["System"]
        # Component type (e.g. 'eTRB0')
        self.type = comp_info["Type"]
        # Display name for CLI (e.g. 'Rorze eTRB0')
        self.display_name = f"Rorze {self.type}"
        # Name of the component in Rorze terms (e.g. 'TRB0')
        self.name = comp_info["Name"]

        self.status = "Initializing..."
        logger.info(f"Initializing {self.display_name}...")
        self.lock = threading.Lock()
        self.busy = False

        self.establish_connection()

    def establish_connection(self,port=12100,retries=1):
        """ Rorze specific connection that opens a socket and waits for an acknowledgement 'CNCT' """
        self.status = "Connecting..."
        logger.info(f"Connecting to {self.display_name}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)

        for i in range(retries+1):

            try:
                self.sock.connect((self.ip, port))
                read = str(self.sock.recv(1024))[2:-3]
                logger.debug(f"Recieved: {read}")

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
        command = f"o{self.name}.ORGN({p1},{p2})"
        message = self.send_and_read_motion(command)
        self.status = f"Origin search completed: {message}"

    def get_rotary_switch_value(self):
        command = f"o{self.name}.GTDT[3]"
        message = self.send_and_read(command).split(":")[1]
        self.status = f"Rotary switch position: {message}"

    def get_status(self):
        command = f"o{self.name}.STAT"
        message = self.send_and_read(command)
        self.status = f"{message}"

    def read_data(self):
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
        command = f"o{self.name}.GTDT[1]"
        message = self.send_and_read(command).split(":")[1]
        system_data["STDT[1]"] = message

        # Get remaining system data
        for field in data_fields:
            command = f"{self.name}.{field}.GTDT"
            message = self.send_and_read(command, buffer=2**21) # 2MiB should always suffice
            system_data[field] = message.split(':')[1]
            self.status = 'Data saved to ./testing/System_data.json'

        with open('testing/System_data.json', 'w') as out:
            json.dump(system_data, out, indent=4)

        def read_block(self, block_name: str, n: Union[int, list[int]], command: str, file: TextIO) -> None:
            name = self.name
            buffer = 2**20
            get_command = f"G{command[1:]}" # Turns STDT into GTDT
            if isinstance(n, int):
                block_range = range(n)
            else:
                block_range = n
            if len(block_range) == 1:
                block = self.send_and_read(f"o{name}.{block_name}.{get_command}",buffer)
                file.write(f"{block_name}.{command}={block}")
            else:
                for i in block_range:
                    block = self.send_and_read(f"o{name}.{block_name}.{get_command}[{i}]",buffer)
                    file.write(f"{block_name}.{command}={block}")

        def read_data_robot(self,filename):
            name = self.name
            buffer = 2**20
            with open(f"{filename}.dat", "w") as backup:
                IP = self.send_and_read(f"o{name}.GTDT[1]", buffer)
                backup.write(f"STDT[1]={IP}")
                DEQU = self.send_and_read(f"o{name}.DEQU.GTDT", buffer)
                backup.write(f"DEQU.STDT={DEQU}")
                DRES = self.send_and_read(f"o{name}.DRES.GTDT", buffer)
                backup.write(f"DRES.STDT={DRES}")
                for i in range(5):
                    DRCI = self.send_and_read(f"o{name}.DRCI.GTDT[{i}]", buffer)
                    backup.write(f"DRCI.STDT[{i}]={DRCI}")
                for i in range(5):
                    DRCS = self.send_and_read(f"o{name}.DRCS.GTDT[{i}]", buffer)
                    backup.write(f"DRCS.STDT[{i}]={DRCS}")
                for i in range(5):
                    DRCH = self.send_and_read(f"o{name}.DRCH.GTDT[{i}]", buffer)
                    backup.write(f"DRCH.STDT[{i}]={DRCH}")
                for i in range(5):
                    DMNT = self.send_and_read(f"o{name}.DMNT.GTDT[{i}]", buffer)
                    backup.write(f"DMNT.STDT[{i}]={DMNT}")
                for i in [0,1,2,3,8,9,10,11,12,13,14,15,16,17,18,19,40]:
                    XAX1 = self.send_and_read(f"o{name}.XAX1.GTDT[{i}]", buffer)
                    backup.write(f"XAX1.STDT[{i}]={XAX1}")
                XAX1 = self.send_and_read(f"o{name}.XAX1.GPRM")
                backup.write(f"XAX1.SPRM={XAX1}")
                for i in range(4):
                    ZAX1 = self.send_and_read(f"o{name}.ZAX1.GTDT[{i}]", buffer)
                    backup.write(f"ZAX1.STDT[{i}]={ZAX1}")
                ZAX1 = self.send_and_read(f"o{name}.ZAX1.GPRM")
                backup.write(f"ZAX1.SPRM={ZAX1}")
                for i in range(4):
                    ROT1 = self.send_and_read(f"o{name}.ROT1.GTDT[{i}]", buffer)
                    backup.write(f"ROT1.STDT[{i}]={ROT1}")
                ROT1 = self.send_and_read(f"o{name}.ROT1.GPRM")
                backup.write(f"ROT1.SPRM={ROT1}")
                for i in range(4):
                    ROT1 = self.send_and_read(f"o{name}.ROT1.GTDT[{i}]", buffer)
                    backup.write(f"ROT1.STDT[{i}]={ROT1}")
                ROT1 = self.send_and_read(f"o{name}.ROT1.GPRM")
                backup.write(f"ROT1.SPRM={ROT1}")
                for i in range(4):
                    ARM1 = self.send_and_read(f"o{name}.ARM1.GTDT[{i}]", buffer)
                    backup.write(f"ARM1.STDT[{i}]={ARM1}")
                ARM1 = self.send_and_read(f"o{name}.ARM1.GPRM")
                backup.write(f"ARM1.SPRM={ARM1}")
                for i in range(4):
                    ARM2 = self.send_and_read(f"o{name}.ARM2.GTDT[{i}]", buffer)
                    backup.write(f"ARM2.STDT[{i}]={ARM2}")
                ARM2 = self.send_and_read(f"o{name}.ARM2.GPRM")
                backup.write(f"ARM2.SPRM={ARM2}")
                for i in range(16):
                    XAX1 = self.send_and_read(f"o{name}.XAX1.GEPM[{i}]", buffer)
                    backup.write(f"XAX1.SEPM[{i}]={XAX1}")
                for i in range(16):
                    ZAX1 = self.send_and_read(f"o{name}.ZAX1.GEPM[{i}]", buffer)
                    backup.write(f"ZAX1.SEPM[{i}]{ZAX1}")
                for i in range(16):
                    ROT1 = self.send_and_read(f"o{name}.ROT1.GEPM[{i}]", buffer)
                    backup.write(f"ROT1.SEPM[{i}]={ROT1}")
                for i in range(16):
                    ARM1 = self.send_and_read(f"o{name}.ARM1.GEPM[{i}]", buffer)
                    backup.write(f"ARM1.SEPM[{i}]={ARM1}")
                for i in range(16):
                    ARM2 = self.send_and_read(f"o{name}.ARM2.GEPM[{i}]", buffer)
                    backup.write(f"ARM2.SEPM[{i}]={ARM2}")
                for i in range(3):
                    DAPM = self.send_and_read(f"o{name}.DAPM.GTDT[{i}]", buffer) 
                    backup.write(f"DAPM.STDT[{i}]={DAPM}")
                for i in range(32):
                    DITK = self.send_and_read(f"o{name}.DITK.GTDT[{i}]", buffer) 
                    backup.write(f"DITK.STDT[{i}]={DITK}")
                for i in range(32):
                    DOUT = self.send_and_read(f"o{name}.DOUT.GTDT[{i}]", buffer) 
                    backup.write(f"DOUT.STDT[{i}]={DOUT}")
                for i in range(400):
                    DTRB = self.send_and_read(f"o{name}.DTRB.GTDA[{i}]", buffer)
                    backup.write(f"DTRB.STDA[{i}]={DTRB}")
                for i in range(400):
                    DTUL = self.send_and_read(f"o{name}.DTUL.GTDA[{i}]", buffer)
                    backup.write(f"DTUL.STDA[{i}]={DTUL}")
                for i in range(400):
                    DMPR = self.send_and_read(f"o{name}.DMPR.GTDT[{i}]", buffer) 
                    backup.write(f"DMPR.STDT[{i}]={DMPR}")
                for i in range(400):
                    DCFG = self.send_and_read(f"o{name}.DCFG.GTDT[{i}]", buffer) 
                    backup.write(f"DCFG.STDT[{i}]={DCFG}")
                for i in range(4):
                    for ii in range(400):
                        DAXM = self.send_and_read(f"o{name}.DAXM.GTDT[{i}][{ii}]", buffer) 
                        backup.write(f"DAXM.STDT[{i}][{ii}]={DAXM}")
                for i in range(32):
                    DSSC = self.send_and_read(f"o{name}.DSSC.GTDT[{i}]", buffer) 
                    backup.write(f"DSSC.STDT[{i}]={DSSC}")
                for i in range(4):
                    DIND = self.send_and_read(f"o{name}.DIND.GTDT[{i}]", buffer) 
                    backup.write(f"DIND.STDT[{i}]={DIND}")

        def read_data_prealigner(self,filename):
            name = self.name
            buffer = 2**21
            with open(f"{filename}.dat", "w") as backup:
                read_block("DRES", 1, "STDT", backup)
                read_block("DEQU", 1, "STDT", backup)
                read_block("DRCS", 5, "STDT", backup)
                read_block("DMNT", 5, "STDT", backup)
                for i in range(5):
                    read_block("DSDB", 4, f"STDT[{i}]", backup)
                read_block("DTMP", 3, "STDT", backup)
                read_block("DCAM", 4, "STDT", backup)
                read_block("DALN", 10, "STDT", backup)
                read_block("DROT", 100, "STDT", backup)
                read_block("DSEN", 10, "STDT", backup)
                read_block("DRCP", 10, "STDT", backup)

class Sinfonia(Component):
    pass