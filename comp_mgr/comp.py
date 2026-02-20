"""
Component Module

All Component data and methods are stored in these class instances

When new components are added, they must be implemented individually here for:
- setting IP address (change_IP)
- setting TCP/IP port (set_host_port)
- setting log host (set_log_host)
- reading a backup (read_data)
"""
import logging
import os
import socket
import sys
import threading
import time
from comp_mgr.exceptions import NoSystem
from datetime import datetime
from typing import TextIO, Union
from comp_mgr.config import NETWORK

logger = logging.getLogger(__name__)

class Component:
    TIMEOUT = 3.0
    MOTION_TIMEOUT = 5.0

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
    
    def establish_connection(self, port=12100, retries=1):
        """
        General attempt to establish connection to a component.
        This method might never be used since the different components have their own class
        """

        self.status = "Connecting..."
        logger.info(f"Connecting to {self.display_name}...")
        logger.debug(f"IP: {self.ip}, System: {self.system}, Name: {self.display_name}, Type: {self.type}")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.TIMEOUT)

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
    
    def recv_until_newline(self, timeout=TIMEOUT):
        self.sock.settimeout(timeout)
        data = b""
        while True:
            chunk = self.sock.recv(1024)
            if not chunk:
                break  # connection closed
            data += chunk
            if (b"\r" in chunk):
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
                message = read
                try:
                    # Simulation always treats it like motion command
                    self.sock.settimeout(self.MOTION_TIMEOUT)
                    self.status = "Waiting for motion..."
                    if "SIMULATION" in self.type:
                        read = self.sock.recv(1024)
                        logger.debug(f"Receive: {read}")
                        message = read 
                except socket.timeout:
                    logger.error("Motion timed out.")
                self.sock.settimeout(self.TIMEOUT)
            except socket.error as e:
                self.status = f"Socket error: {e}"
                logger.error(f"Socket error: {e}")
            finally:
                self.busy = False
        
        self.status = f"Output: {message}"

        return message

    def send_and_read_data(self,command,buffer=2**21):
        
        with self.lock:
            self.busy = True
            self.sock.sendall(command.encode('utf-8'))
            logger.debug(f"Sending: {command}")
            read = str(self.sock.recv(buffer))[2:-3]
            message = read #.split('.')[1]
            self.status = "Reading data..."
            logger.debug(f"Reading data... {message}")
            # Wait until reading finishes finishes
            try: 
                self.sock.settimeout(self.TIMEOUT)
                read = str(self.sock.recv(buffer))[2:-3]
                logger.debug(f"Reading data... {message}")
                message = read #.split('.')[1]
            except socket.timeout:
                self.status = "ERROR: Reading timeout"
                logger.error(f"Reading timeout")
            except socket.error as e:
                self.status = f"Socket error: {e}"
                logger.error(f"Socket error: {e}")
            finally:
                self.busy = False
            
            self.status = f"Reading completed. {message}"
            logger.info(f"Reading completed. {message}")

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
                self.sock.settimeout(self.MOTION_TIMEOUT)
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
        # Serial number of the component (if it exists)
        self.sn = comp_info["SN"]
        # Component Type (e.g. "RA320_003")
        self.identifier = comp_info["Identifier"]
        # Firmware Version
        self.firmware = comp_info["Firmware"]

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
        self.sock.settimeout(self.TIMEOUT)

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
    
    def read_name(self):
        """
        Rorze components will have a prefix that contain type information.
        This prefix has to have a character removed, such that commands can be sent.
        Example: extended_type="eTRB0" -> type="TRB0"
        """
        if self.name == "SIM1":
            name = "SIMULATIONeTRB0"
        else:
            name = "o"+self.name[-4:]
        return name

    def origin_search(self, p1: int=0, p2: int=0):
        command = f"{self.read_name()}.ORGN({p1},{p2})"
        message = self.send_and_read_motion(command)
        self.status = f"Origin search completed: {message}"

    def get_rotary_switch_value(self):
        command = f"{self.read_name()}.GTDT[3]"
        message = self.send_and_read(command)
        self.status = f"Rotary switch position: {message}"

    def get_status(self):
        command = f"{self.read_name()}.STAT"
        message = self.send_and_read(command)
        self.status = f"{message}"

    def change_IP(self, ip):
        # Implement different component types here
        if self.identifier in ["RR754", "RTS13", "RV201-F07-000", "SIM_COMPONENT"]:
            command = f"{self.read_name()}.STDT[1]={ip}"
        elif self.identifier in ["RA320_003", "RA420_001"]: #TODO Verify RA420
            command = f"{self.read_name()}.DEQU.STDT[3]={ip}"
        else:
            status = f"Component type {self.identifier} has not been implemented"
            self.status = status
            logger.error(status)
            return

        message = self.send_and_read(command)
        self.sock.settimeout(self.MOTION_TIMEOUT)
        write = self.send_and_read(f"{self.read_name()}.WTDT")
        self.sock.settimeout(self.TIMEOUT)
        #TODO read acknowledge 
        self.status = f"IP set to {ip}. Please restart the component. ({message})"

    def get_host_IP(self):
        command = f"{self.read_name()}.DEQU.GTDT[1]"
        ip = self.send_and_read(command)
        return ip
    
    def get_host_port(self):
        if self.identifier in ["RV201-F07-000", "RR754", "RTS13", "SIM_COMPONENT"]:
            command = f"{self.read_name()}.DEQU.GTDT[68]"
            port = self.send_and_read(command)
            return port
        elif self.identifier in ["RA320","RA320_003", "RA420_001"]:
            command = f"{self.read_name()}.DEQU.GTDT[2]"
            port = self.send_and_read(command)
            return port
        else:
            return None
        
    def get_log_host(self):
        if self.identifier in ["RV201-F07-000", "RR754", "RTS13", "SIM_COMPONENT"]:
            command = f"{self.read_name()}.DEQU.GTDT[69]"
            ip = self.send_and_read(command)
            return ip
        elif self.identifier in ["RA320","RA320_003", "RA420_001"]:
            command = f"{self.read_name()}.DEQU.GTDT[4]"
            ip = self.send_and_read(command)
            return ip
        else:
            return None

    def set_host_IP(self,ip):
        command = f"{self.read_name()}.DEQU.STDT[1]={ip}"
        self.send_and_read(command)
        self.sock.settimeout(self.MOTION_TIMEOUT)
        write = self.send_and_read(f"{self.read_name()}.WTDT")
        self.sock.settimeout(self.TIMEOUT)
        #TODO read acknowledge 
        self.status = f"Host IP set to {ip}."
    
    def set_host_port(self,port):
        if self.identifier in ["RV201-F07-000", "RR754", "RTS13", "SIM_COMPONENT"]:
            command = f"{self.read_name()}.DEQU.STDT[68]={port}"
            self.send_and_read(command)
            self.sock.settimeout(self.MOTION_TIMEOUT)
            write = self.send_and_read(f"{self.read_name()}.WTDT")
            self.sock.settimeout(self.TIMEOUT)
            #TODO read acknowledge 
        elif self.identifier in ["RA320","RA320_003", "RA420_001"]:
            command = f"{self.read_name()}.DEQU.STDT[2]={port}"
            self.send_and_read(command)
            self.sock.settimeout(self.MOTION_TIMEOUT)
            write = self.send_and_read(f"{self.read_name()}.WTDT")
            self.sock.settimeout(self.TIMEOUT)
            #TODO read acknowledge 
        else:
            status = f"Component type {self.identifier} has not been implemented"
            self.status = status
            logger.error(status)
            return

        self.status = f"TCP/IP port set to {port}."
    
    #TODO IMPLEMENT ALL OTHER AUTOSETUP METHODS HERE
        
    def set_log_host(self,ip):
        if self.identifier in ["RV201-F07-000", "RR754", "RTS13", "SIM_COMPONENT"]:
            command = f"{self.read_name()}.DEQU.STDT[69]={ip}"
            self.send_and_read(command)
            self.sock.settimeout(self.MOTION_TIMEOUT)
            write = self.send_and_read(f"{self.read_name()}.WTDT")
            self.sock.settimeout(self.TIMEOUT)
            #TODO read acknowledge 
        elif self.identifier in ["RA320","RA320_003", "RA420_001"]:
            command = f"{self.read_name()}.DEQU.STDT[4]={ip}"
            self.send_and_read(command)
            self.sock.settimeout(self.MOTION_TIMEOUT)
            write = self.send_and_read(f"{self.read_name()}.WTDT")
            self.sock.settimeout(self.TIMEOUT)
            #TODO read acknowledge 
        else:
            status = f"Component type {self.identifier} has not been implemented"
            self.status = status
            logger.error(status)
            return

        self.status = f"Log host set to {ip}."

    def GAIO(self):
        command = f"{self.read_name()}.GAIO"
        message = self.send_and_read(command)
        self.status = f"Response logged."

    def SAIO_on(self):
        command = f"{self.read_name()}.SAIO(00000000000000000000000100000010,00000000000000000000000000000000,0000000000)"
        message = self.send_and_read(command)
        #TODO read acknowledge 
        self.status = f"Automatic status ON. Response logged."

    def SAIO_off(self):
        command = f"{self.read_name()}.SAIO(00000000000000000000000000000000,00000000000000000000000000000000,0000000000)"
        message = self.send_and_read(command)
        #TODO read acknowledge 
        self.status = f"Automatic status OFF. Response logged."
    
    def set_laser(self, arm, setting):
        if arm == 'lower':
            arm_no = 2
            if setting == 'on':
                set_bit = 'D080B'
            elif setting == 'off':
                set_bit = 'D081B'
        elif arm == 'upper':
            arm_no = 1
            if setting == 'on':
                set_bit = 'D100B'
            elif setting == 'off':
                set_bit = 'D101B'
        command = f"{self.read_name()}.ARM{arm_no}.DCMD({set_bit},1)"
        message = self.send_and_read(command)
        self.GAIO()
        self.status = f"{arm} arm laser turned {setting}"
    
    def basic_settings(self):
        """
        Basic settings to change for every component
        - TCP/IP Port
        - Host IP Address
        - Log Host
        + Component-Specific Stuff
        """
        # System-Specific settings
        host_ip = "255.255.255.255"
        port = 12000
        if self.system == "WMC":
            log_host = "192.168.30.1"
        elif self.system == "SEMDEX":
            log_host = "192.168.0.10"
        else:
            logger.error("No system found in configuration")
            raise NoSystem

        # Component-specific settings
        if self.identifier == "RV201-F07-000":
            logger.info("Changing the following Loadport settings: TCP/IP Port | Host IP | Log Host | Auto Output | Presence LED | I/O")
            self.auto_output() #TODO
            self.presence_led() #TODO
            self.io() #TODO
        
        elif self.identifier in ["RA320", "RA420_001", "RA320_003"]:
            logger.info("Changing the following Prealigner settings: TCP/IP Port | Host IP | Log Host | Host Interface | Body no")
            self.host_interface() #TODO
            self.set_body_no(1) #TODO

        elif self.identifier == "RR754":
            logger.info("Changing the following Robot settings: TCP/IP Port | Host IP | Log Host | No Interpolation")
            self.no_interpolation() #TODO
        
        elif self.identifier == "RTS13":
            logger.info("Changing the following Lineartrack settings: TCP/IP Port | Host IP | Log Host")

        # Common Settings
        self.set_host_port(port)
        self.set_host_IP(host_ip)
        self.set_log_host(log_host)

    def read_data(self):
        """
        This serves the same purpose as the 'Read Data' button in the
        Rorze maintenance software. It is slightly different for each component.
        """

        def read_block(self,
                       block_name: str,
                       n: Union[int, list[int]],
                       set_command: str,
                       file: TextIO,
                       add_brackets: bool=False) -> None:
            """"Reads one block of component data, like 5 lines of DRCS for the Robot"""
            name = self.name
            buffer = 2**20
            get_command = f"G{set_command[1:]}" # Turns STDT into GTDT

            # Turn the input of n into a list, even if it has just one element
            if isinstance(n, int):
                block_range = range(n)
            else:
                block_range = n

            if len(block_range) == 1:
                block = self.send_and_read(f"o{name}.{block_name}.{get_command}",buffer)

                # Cut Prefix from block
                prefix = f"a{name}.{block_name}.{get_command}:"
                if not prefix == block[:len(prefix)]:
                    e = f"Mismatch between sent command and received command: {block}"
                    logger.error(e)
                    raise Exception(e)
                block = block[len(prefix):]

                # Add [0], if this is required (Lineartrack does this) #TODO Test this!
                if add_brackets:
                    set_string = f"{block_name}.{set_command}[0]={block}"
                else:
                    set_string = f"{block_name}.{set_command}={block}"
                
                # Write to file
                print(set_string, file=file)
                # file.write(f"{block_name}.{command}={block}\n")

            else:
                for i in block_range:
                    block = self.send_and_read(f"o{name}.{block_name}.{get_command}[{i}]",buffer)

                    # Cut Prefix from block
                    prefix = f"a{name}.{block_name}.{get_command}:"
                    if not prefix == block[:len(prefix)]:
                        e = f"Mismatch between sent command and received command: {block}"
                        logger.error(e)
                        raise Exception(e)
                    block = block[len(prefix):]

                    # Write to file
                    print(f"{block_name}.{set_command}[{i}]={block}", file=file)
                    # file.write(f"{block_name}.{command}={block}\n")

        def read_data_robot(self,filename):
            name = self.name
            buffer = 2**20
            with open(f"{filename}", "w") as backup:
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
            """
            This is for the standard no-vaccuum spindle prealigner.
            Other prealigners will have different backup procedures.
            """
            with open(f"{filename}", "w") as backup:
                read_block(self,"DRES", 1, "STDT", backup)
                read_block(self,"DEQU", 1, "STDT", backup)
                read_block(self,"DRCS", 5, "STDT", backup)
                read_block(self,"DMNT", 5, "STDT", backup)
                for i in range(5):
                    read_block(self, "DSDB", 4, f"STDT[{i}]", backup)
                read_block(self, "DTMP", 3, "STDT", backup)
                read_block(self, "DCAM", 4, "STDT", backup)
                read_block(self, "DALN", 10, "STDT", backup)
                read_block(self, "DROT", 100, "STDT", backup)
                read_block(self, "DSEN", 10, "STDT", backup)
                read_block(self, "DRCP", 10, "STDT", backup)

        def read_data_loadport(self,filename):
            with open(f"{filename}", "w") as backup:

                # Read IP and cut Prefix from IP
                IP = self.send_and_read(f"o{self.name}.GTDT[1]", 1000)
                prefix = f"a{self.name}.GTDT:"
                if not prefix == IP[:len(prefix)]:
                    e = f"Mismatch between sent command and received command: {IP}"
                    logger.error(e)
                    raise Exception(e)
                IP = IP[len(prefix):]
                print(f"STDT[1]={IP}", file=backup)

                read_block(self, "DEQU", 1, "STDT", backup)
                read_block(self, "DRES", 1, "STDT", backup)
                read_block(self, "DRCI", 2, "STDT", backup)
                read_block(self, "DRCS", 2, "STDT", backup)
                read_block(self, "DMNT", 2, "STDT", backup)
                read_block(self, "YAX1", 4, "STDT", backup)
                read_block(self, "YAX1", 1, "SPRM", backup)
                read_block(self, "ZAX1", 4, "STDT", backup)
                read_block(self, "ZAX1", 1, "SPRM", backup)
                read_block(self, "DSTG", 1, "STDT", backup)
                read_block(self, "DMPR", 1, "STDT", backup)
                read_block(self, "DPRM", 64, "STDT", backup)
                read_block(self, "DCST", 1, "STDT", backup)
                read_block(self, "DE84", 1, "STDT", backup)
        
        def read_data_lineartrack(self,filename):
            with open(f"{filename}", "w") as backup:
                read_block(self,"DEQU", 1, "STDT", backup)
                read_block(self,"DRES", 1, "STDT", backup)
                read_block(self,"DRCI", 1, "STDT", backup, add_brackets=True)
                read_block(self,"DRCS", 1, "STDT", backup, add_brackets=True)
                read_block(self,"DRCH", 1, "STDT", backup, add_brackets=True)
                read_block(self,"DMNT", 1, "STDT", backup, add_brackets=True)
                read_block(self,"XAX1", [0,1,2,8,9,10,11,12,13,14,15,16,17,18,19,40], "STDT", backup)
                read_block(self,"XAX1", 1, "SPRM", backup)
                read_block(self,"XAX1", 16, "SEPM", backup)
                read_block(self,"DTBL", 400, "STDA", backup)

        # Timestamp
        ts = datetime.now().strftime("%Y%m%d")
        index = 0
        filename = f"{self.sn}_{ts}_{index}.dat"
        logger.debug(f"Reading data to {filename}")

        # Make sure to not overwrite a previous backup
        file_exists = 1 if os.path.exists(filename) else 0
        while file_exists:
            index+=1
            filename = f"{self.sn}_{ts}_{index}.dat"
            logger.warning(f"File exists! Changing filename to {filename}")
            if not os.path.exists(filename):
                break

        try: 
            if self.identifier == "RV201-F07-000":
                logger.info(f"Starting Loadport Backup for {self.name}.")
                read_data_loadport(self, filename)
            elif self.identifier == "RR754":
                logger.info(f"Starting Robot Backup for {self.name}")
                read_data_robot(self, filename)
            elif self.identifier in ["RA320", "RA420_001", "RA320_001"]:
                logger.info(f"Starting Prealigner Backup for {self.name}")
                read_data_prealigner(self, filename) # TODO add other prealigners than RA320_003
            elif self.identifier == "RTS13":
                logger.info(f"Starting Linear Track Backup for {self.name}")
                read_data_lineartrack(self, filename) # TODO add other prealigners than RA320_003
            else:
                error = f"Backup not implemented for component {self.identifier}"
                logger.error(error)
                raise Exception(error)
            self.status = f"Backup saved to '{filename}'"
        except Exception as e:
            logger.error(f"Reading failed: {e}")
            self.status = {f"Reading failed: {e}"}