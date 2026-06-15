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
import ipaddress
import os
import socket
import sys
import threading
from comp_mgr.exceptions import NoSystem, Unhandled
from datetime import datetime
from pathlib import Path
from typing import TextIO, Union
from comp_mgr.config import PREALIGNERS, LOADPORTS, ROBOTS, OTHER

logger = logging.getLogger(__name__)
    
class Rorze():

    TIMEOUT = 1
    MOTION_TIMEOUT = 12
    CNCT_TIMEOUT = 5

    def __init__(self, comp_info: dict, simulation:bool = False):
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

        self.simulation = simulation

        self.status = "Initializing..."
        logger.info(f"Initializing {self.display_name}...")
        self.lock = threading.Lock()
        self.busy = False

        self.establish_connection(self.simulation)

    def establish_connection(self,port=12100):

        if self.simulation:
            logger.warning("Simulation mode, generating data from config dict!")
            return

        """ Rorze specific connection that opens a socket and waits for an acknowledgement 'CNCT' """
        self.status = "Connecting..."
        logger.info(f"Connecting to {self.display_name}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.CNCT_TIMEOUT)
        try:
            logger.debug(f"Rorze.establish_connection() -> Connecting to {self.ip}:{port}")
            self.sock.connect((self.ip, port))
            read = str(self.sock.recv(1024))[2:-3]
            logger.debug(f"Rorze.establish_connection() -> Recieved: {read}")

            # Store component type!
            self.type = read.split('.')[0]

            message = read.split('.')[1]

            if "CNCT" in message:
                self.status = f"{self.type} is connected"
                logger.info(f"Connection to {self.display_name} successful")
        except socket.timeout:
            self.status = "ERROR: Connection Timeout"
            logger.error("Connection Timeout")
            self.busy = True
        except socket.error as e:
            self.busy = True
            self.status = f"Socket error: {e}"
            logger.error(f"Socket error: {e}")
        finally:
            self.busy = False

        self.sock.settimeout(self.TIMEOUT)

    def close_connection(self):
        self.sock.close()
    
    def recv_until_newline(self):
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
        command = f"{command}\r" # \r required to send

        if self.simulation:
            logger.debug(f"(SIM) Sending: {command}")
            return "(SIM) Response"

        with self.lock:
            self.busy = True
            logger.debug(f"Sending: {command}")
            self.sock.sendall(command.encode('utf-8')) 
            try: 
                read = self.recv_until_newline()
                logger.debug(f"Receive: {read}")
                message = read
            except socket.error as e:
                self.status = f"Socket error: {e}"
                logger.error(f"Socket error: {e}")
            finally:
                self.busy = False
        
        return message

    # Motion commands - not planned yet
    # def send_and_read_motion(self,command,buffer=1024):
        
    #     with self.lock: # THIS SHOULD NOT BLOCKING -- EMO NEEDS TO BE POSSIBLE
    #         self.busy = True
    #         logger.debug(f"Sending: {command}")
    #         self.sock.sendall(command.encode('utf-8'))
    #         try: 
    #             read = self.recv_until_newline()
    #             message = read #.split('.')[1]
    #             self.status = "Component is in motion..."
    #             logger.debug(f"Component is in motion... {message}")
    #             self.sock.settimeout(self.MOTION_TIMEOUT)
    #             read = self.recv_until_newline()
    #             message = read #.split('.')[1]
    #         except socket.timeout:
    #             self.status = "ERROR: Motion timeout"
    #             logger.error(f"Motion timeout")
    #         except socket.error as e:
    #             self.status = f"Socket error: {e}"
    #             logger.error(f"Socket error: {e}")
    #         finally:
    #             self.busy = False
            
    #         self.status = f"Motion completed {message}"
    #         logger.info(f"Motion completed {message}")

    #     return message
    
    def read_name(self):
        """
        Rorze components will have a prefix that contain type information.
        This prefix has to have a character removed, such that commands can be sent.
        Example: extended_type="eTRB0" -> type="TRB0"
        """
        name = "o"+self.name[-4:]
        return name

    # ========== Define commands here ==========

    def basic_settings(self, write=1):
        """
        Basic settings to change for every component
        - TCP/IP Port
        - Host IP Address
        - Log Host
        + Component-Specific Stuff
        """
        # System-Specific settings
        host_ip = -1
        port = 12000
        if self.system == "WMC":
            log_host = "192.168.30.1"
        elif self.system == "SEMDEX":
            log_host = "192.168.0.10"
        else:
            logger.error("No system found in configuration")
            raise NoSystem

        # Component-specific settings
        if self.identifier in LOADPORTS:
            logger.info("Changing the following Loadport settings: TCP/IP Port | Host IP | Log Host | Auto Output | Presence LED | I/O")
            self.set_loadport_settings(write)
        
        elif self.identifier in PREALIGNERS:
            logger.info("Changing the following Prealigner settings: TCP/IP Port | Host IP | Log Host | Host Interface | Body no")
            self.set_host_interface(write)
            self.set_body_no(1,write)

        elif self.identifier in ROBOTS:
            logger.info("Changing the following Robot settings: TCP/IP Port | Host IP | Log Host")
        
        elif self.identifier == "RTS13":
            logger.info("Changing the following Lineartrack settings: TCP/IP Port | Host IP | Log Host")

        # Common Settings
        self.set_host_IP(host_ip, write)
        self.set_host_port(port, write)
        self.set_log_host(log_host, write)

    def change_IP(self, ip, write=1):
        # Implement different component types here
        if any(self.identifier in lst for lst in [ROBOTS, LOADPORTS, OTHER]):
            command = f"{self.read_name()}.STDT[1]={ip}"
        elif self.identifier in PREALIGNERS:
            command = f"{self.read_name()}.DEQU.STDT[3]={ip}"
        else:
            status = f"Component type {self.identifier} has not been implemented"
            self.status = status
            logger.error(status)
            return

        message = self.send_and_read(command)
        if write: self.write_changes()
        self.status = f"IP set to {ip}. Please restart the component. ({message})"
    
    def convert_IP(self, ip):
        """Convert ip from string into Rorze int format, in which octets are reversed"""
        # Convert "1.2.3.4" into int("4.3.2.1")
        new_ip_int = int(ipaddress.IPv4Address(".".join(f'{ip}'.split('.')[::-1])))
        return new_ip_int

    def GAIO(self):
        command = f"{self.read_name()}.GAIO"
        message = self.send_and_read(command)
        self.status = message

    def get_backup_dir(self):
        """Makes sure, that Pyinstaller doesn't reset the cwd"""
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).resolve().parent.parent

    def get_host_IP(self):
        command = f"{self.read_name()}.DEQU.GTDT[1]"
        ip = self.send_and_read(command)
        return ip

    def get_host_port(self):
        if any(self.identifier in lst for lst in [ROBOTS, LOADPORTS, OTHER]):
            command = f"{self.read_name()}.DEQU.GTDT[68]"
            port = self.send_and_read(command)
            return port
        elif self.identifier in PREALIGNERS:
            command = f"{self.read_name()}.DEQU.GTDT[2]"
            port = self.send_and_read(command)
            return port
        else:
            return None

    def get_log_host(self):
        if any(self.identifier in lst for lst in [ROBOTS, LOADPORTS, OTHER]):
            command = f"{self.read_name()}.DEQU.GTDT[69]"
            ip = self.send_and_read(command)
            return ip
        elif self.identifier in PREALIGNERS:
            command = f"{self.read_name()}.DEQU.GTDT[4]"
            ip = self.send_and_read(command)
            return ip
        else:
            return None

    def get_rotary_switch_value(self):
        command = f"{self.read_name()}.GTDT[3]"
        message = self.send_and_read(command)
        self.status = f"Rotary switch position: {message}"

    def get_status(self):
        command = f"{self.read_name()}.STAT"
        message = self.send_and_read(command)
        self.status = f"{message}"

    def no_interpolation(self, write=1):
        self.busy=True
        self.status="Applying no interpolation..."
        case_1 = '"","","","","",00003,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000'
        case_2 = '"","","","","",00000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000,+0000000000'
        for idx in range(400):
            command = f"{self.read_name()}.DCFG.STDT[{idx}]="
            if idx in [0,10,11,12,13]:
                command+=case_1
            else:
                command+=case_2
            self.send_and_read(command)
        if write: self.write_changes()
        self.busy=False
    
    def origin_search(self, p1: int=0, p2: int=0):
        command = f"{self.read_name()}.ORGN({p1},{p2})"
        message = self.send_and_read_motion(command)
        self.status = f"Origin search completed: {message}"

    def SAIO_on(self):
        command = f"{self.read_name()}.SAIO(00000000000000000000000100000010,00000000000000000000000000000000,0000000000)"
        message = self.send_and_read(command)
        logger.debug(message)
        self.status = "Automatic status ON. Response logged."

    def SAIO_off(self):
        command = f"{self.read_name()}.SAIO(00000000000000000000000000000000,00000000000000000000000000000000,0000000000)"
        message = self.send_and_read(command)
        logger.debug(message)
        self.status = "Automatic status OFF. Response logged."

    def set_aligner_speed(self, speed, write=1):
        if speed == "Slow":
            alignment_acceleration = 100000
            alignment_speed = 30000
        elif speed == "Normal":
            # Leave as is, unless the speed has been set to slow before!
            command = f"{self.read_name()}.DRCS.GTDT[003][10]"
            alignment_acceleration = self.send_and_read(command)
            command = f"{self.read_name()}.DRCS.GTDT[003][11]"
            alignment_speed = self.send_and_read(command)
            if alignment_acceleration == 100000 and alignment_speed == 30000:
                logger.warning("Detected slow aligner setting. Restoring speed parameter.")
                alignment_acceleration = 450000
                alignment_speed = 120000
            else:
                return

        # Set acceleration for alignment operation
        command = f"{self.read_name()}.DRCS.STDT[003][10]={alignment_acceleration}"
        self.send_and_read(command)
        # Set speed for alignment operation
        command = f"{self.read_name()}.DRCS.STDT[003][11]={alignment_speed}"
        self.send_and_read(command)
        # Set deceleration for alignment operation
        command = f"{self.read_name()}.DRCS.STDT[003][12]={alignment_acceleration}"
        self.send_and_read(command)
        logger.info(f"Setting aligner speed to {alignment_speed} and acceleration to {alignment_acceleration}")
        if write: self.write_changes()
    
    def set_body_no(self, body_no, write=1):
        if any(self.identifier in lst for lst in [ROBOTS, LOADPORTS, PREALIGNERS]):
            command = f"{self.read_name()}.DEQU.STDT[6]={body_no}"
            self.send_and_read(command)

            # If Body No. >1 - Also change IP
            if body_no > 1:
                logger.info("Setting IP according to Body No")
                if self.system == "WMC":
                    self.change_IP(f"192.168.30.1{body_no}0")
                elif self.system == "SEMDEX":
                    self.change_IP(f"192.168.0.2{body_no}")
            if write: self.write_changes()
        else:
            status = f"Component type {self.identifier} has not been implemented"
            self.status = status
            logger.error(status)
            return
        self.status = f"Body no set to {body_no}"

    def set_flip_near(self, setting, write=1):
        software_switch = self.send_and_read(f"{self.read_name()}.DEQU.GTDT[8]")
        logger.debug(f"Software_switch before cutting: {software_switch}")
        software_switch = int(software_switch.split(":")[1])
        logger.debug(f"Software_switch after cutting: {software_switch}")
        # Flip the 28th bit, which corresponds to the 'flip finger near' setting
        if setting == "Off":
            software_switch |= (1 << 28)
        elif setting == "On":
            software_switch &= ~(1 << 28)
        else:
            logger.error("Unhandled exception")
            raise Unhandled
        self.send_and_read(f"{self.read_name()}.DEQU.STDT[8]={software_switch}")
        logger.info(f"Setting robot software switch to {software_switch}")
        if write: self.write_changes()
    
    def set_host_interface(self, write=1):
        command = f"{self.read_name()}.DEQU.STDT[5]=001"
        self.send_and_read(command)
        if write: self.write_changes()
    
    def set_host_IP(self, ip, write=1):
        command = f"{self.read_name()}.DEQU.STDT[1]={ip}"
        self.send_and_read(command)
        if write: self.write_changes()
        self.status = f"Host IP set to {ip}."
    
    def set_host_port(self, port, write=1):
        if any(self.identifier in lst for lst in [ROBOTS, LOADPORTS, OTHER]):
            command = f"{self.read_name()}.DEQU.STDT[68]={port}"
            self.send_and_read(command)
            if write: self.write_changes()
        elif self.identifier in PREALIGNERS:
            command = f"{self.read_name()}.DEQU.STDT[2]={port}"
            self.send_and_read(command)
            if write: self.write_changes()
        else:
            status = f"Component type {self.identifier} has not been implemented"
            self.status = status
            logger.error(status)
            return

        self.status = f"TCP/IP port set to {port}."
    
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
        self.status = f"{arm} arm laser turned {setting}. ({message})"
    
    def set_loadport_settings(self, write=1):
        """Sets the bits for system data according to checklists (last updated: 2026-02-20)"""
        if self.identifier == "RV201-F07-000":
            # Sets bits 18 (Presence LED) 4 (Auto Output) and 3 (I/O)
            command = f"{self.read_name()}.DEQU.STDT[8]=299129"
            self.send_and_read(command)
            if write: self.write_changes()
            self.status = "Set basic loadport settings"
    
    def set_log_host(self, ip, write=1):
        if self.identifier in PREALIGNERS:
            command = f"{self.read_name()}.DEQU.STDT[4]={ip}"
            self.send_and_read(command)
            if write: self.write_changes()
        elif any(self.identifier in lst for lst in [ROBOTS, LOADPORTS, OTHER]):
            # Convert ip to int following rorze method
            ip_int = self.convert_IP(ip)
            command = f"{self.read_name()}.DEQU.STDT[69]={ip_int}"
            self.send_and_read(command)
            if write: self.write_changes()
        else:
            status = f"Component type {self.identifier} has not been implemented"
            self.status = status
            logger.error(status)
            return

        self.status = f"Log host set to {ip}."

    def set_notch_angle(self, notch_angle, write=1):
        if self.identifier == "RA320_003":
            command = f"{self.read_name()}.DALN.STDT[0][17]={notch_angle}"
            self.send_and_read(command)
        elif self.identifier in ["RA320_002", "RA321_001"]:
            command = f"{self.read_name()}.DALN.STDT[0][14]={notch_angle}"
            self.send_and_read(command)
        elif self.identifier == "RA420_001":
            for work in range(3):
                command = f"{self.read_name()}.DALN.STDT[{work}][14]={notch_angle}"
                self.send_and_read(command)
        if write: self.write_changes()
    
    def spindle_fix(self, write=1):
        command = f"{self.read_name()}.DALN.STDT[0][37]=100"
        self.send_and_read(command)
        command = f"{self.read_name()}.DALN.STDT[0][38]=100"
        self.send_and_read(command)
        if write: self.write_changes()

    def write_changes(self):
        self.status = "Writing to flash memory..."
        if self.simulation:
            return
        self.sock.settimeout(60)
        acknowledge = self.send_and_read(f"{self.read_name()}.WTDT")
        logger.debug(f"Writing data to flash memory: {acknowledge}")
        self.status = "Changes saved to flash memory."
        self.sock.settimeout(self.TIMEOUT)
    
    def read_data(self, suffix=""):
        """
        This serves the same purpose as the 'Read Data' button in the
        Rorze maintenance software. It is slightly different for each component.
        """
        self.status = "Reading data..."
        
        def read_ip_prefix(self, file):
            IP = self.send_and_read(f"o{self.name}.GTDT[1]", 1000)
            prefix = f"a{self.name}.GTDT:"
            if not prefix == IP[:len(prefix)]:
                e = f"Mismatch between sent command and received command: {IP}"
                raise Exception(e)
            IP = IP[len(prefix):]
            print(f"STDT[1]={IP}", file=file)

        def read_block(self,
                       block_name: str,
                       n: Union[int, list[int]],
                       set_command: str,
                       file: TextIO,
                       add_brackets: bool=False,
                       add_leading: bool=False) -> None:
            """"Reads one block of component data, e.g. 5 lines of DRCS for the Robot"""
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
                prefix = f"a{name}.{block_name}.{get_command[:4]}:" # Cuts the bracket of the get command GTDT[000]
                if not prefix == block[:len(prefix)]:
                    e = f"Mismatch between sent command and received command: {block} / {prefix}"
                    raise Exception(e)
                block = block[len(prefix):]

                set_string = f"{block_name}.{set_command}={block}"
                
                # Write to file
                print(set_string, file=file)

            else:
                for i in block_range:
                    if add_leading:
                        idx = f"{i:03}"
                    else:
                        idx = i
                    block = self.send_and_read(f"o{name}.{block_name}.{get_command}[{idx}]",buffer)

                    # Cut Prefix from block
                    prefix = f"a{name}.{block_name}.{get_command[:4]}:" # Cuts the bracket of the get command GTDT[000]
                    if not prefix == block[:len(prefix)]:
                        e = f"Mismatch between sent command and received command: {block} / {prefix}"
                        raise Exception(e)
                    block = block[len(prefix):]

                    # Write to file
                    print(f"{block_name}.{set_command}[{idx}]={block}", file=file)

        def read_data_lineartrack(self,filename):
            with open(f"{filename}", "x") as backup:
                read_block(self,"DEQU", 1, "STDT", backup)
                read_block(self,"DRES", 1, "STDT", backup)
                read_block(self,"DRCI", 1, "STDT[0]", backup, add_brackets=True) # Lineartrack needs extra [0]
                read_block(self,"DRCS", 1, "STDT[0]", backup, add_brackets=True)
                read_block(self,"DRCH", 1, "STDT[0]", backup, add_brackets=True)
                read_block(self,"DMNT", 1, "STDT[0]", backup, add_brackets=True)
                read_block(self,"XAX1", [0,1,2,8,9,10,11,12,13,14,15,16,17,18,19,40], "STDT", backup)
                read_block(self,"XAX1", 1, "SPRM", backup)
                read_block(self,"XAX1", 16, "SEPM", backup)
                read_block(self,"DTBL", 400, "STDA", backup)

        def read_data_loadport(self,filename):
            with open(f"{filename}", "x") as backup:
                read_ip_prefix(self, backup)
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
        
        def read_data_prealigner(self, filename):
            with open(f"{filename}", "x") as backup:
                if self.identifier == "RA320_002":
                    read_block(self,"DRES", 1, "STDT", backup, add_leading=True)
                    read_block(self,"DEQU", 1, "STDT", backup, add_leading=True)
                    read_block(self,"DRCS", 4, "STDT", backup, add_leading=True)
                    read_block(self,"DMNT", 4, "STDT", backup, add_leading=True)
                    for i in range(5):
                        read_block(self, "DSDB", 3, f"STDT[{i:03}]", backup, add_leading=True)
                    read_block(self, "DTMP", 1, "STDT", backup, add_leading=True)
                    read_block(self, "DALN", 10, "STDT", backup, add_leading=True)
                    read_block(self, "DROT", 100, "STDT", backup, add_leading=True)
                    read_block(self, "DPRS", 1, "STDT", backup, add_leading=True)
                    read_block(self, "DSEN", 10, "STDT", backup, add_leading=True)
                    read_block(self, "DRCP", 10, "STDT", backup, add_leading=True)

                elif self.identifier == "RA320_003":
                    read_block(self,"DRES", 1, "STDT", backup, add_leading=True)
                    read_block(self,"DEQU", 1, "STDT", backup, add_leading=True)
                    read_block(self,"DRCS", 4, "STDT", backup, add_leading=True)
                    read_block(self,"DMNT", 4, "STDT", backup, add_leading=True)
                    for i in range(5):
                        read_block(self, "DSDB", 3, f"STDT[{i:03}]", backup, add_leading=True)
                    read_block(self, "DTMP", 1, "STDT", backup, add_leading=True)
                    read_block(self, "DCAM", 4, "STDT", backup, add_leading=True)
                    read_block(self, "DALN", 10, "STDT", backup, add_leading=True)
                    read_block(self, "DROT", 100, "STDT", backup, add_leading=True)
                    read_block(self, "DSEN", 10, "STDT", backup, add_leading=True)
                    read_block(self, "DRCP", 10, "STDT", backup, add_leading=True)

                elif self.identifier == "RA420_001":
                    read_block(self,"DEQU", 1, "STDT", backup, add_leading=True)
                    read_block(self,"DRCS", 4, "STDT", backup, add_leading=True)
                    read_block(self,"DSAX", 10, "STDT", backup, add_leading=True)
                    read_block(self,"DSAY", 10, "STDT", backup, add_leading=True)
                    read_block(self,"DSAZ", 10, "STDT", backup, add_leading=True)
                    read_block(self,"DSAR", 10, "STDT", backup, add_leading=True)
                    read_block(self,"DMNT", 4, "STDT", backup, add_leading=True)
                    read_block(self,"DRES", 1, "STDT", backup, add_leading=True)
                    for i in range(5):
                        read_block(self,"DSDB", 3, f"STDT[{i:03}]", backup, add_leading=True)
                    read_block(self,"DTMP", 1, "STDT", backup, add_leading=True)
                    read_block(self,"DCAM", 4, "STDT", backup, add_leading=True)
                    read_block(self,"DAWS", 1, "STDT", backup, add_leading=True)
                    read_block(self,"DALN", 8, "STDT", backup, add_leading=True)
                    read_block(self,"DROT", 10, "STDT", backup, add_leading=True)
                    read_block(self,"DPRS", 1, "STDT", backup, add_leading=True)
                    read_block(self,"DSEN", 10, "STDT", backup, add_leading=True)
                    read_block(self,"DRCP", 10, "STDT", backup, add_leading=True)
                    read_block(self,"DITK", 64, "STDT", backup, add_leading=True)
                    read_block(self,"DOUT", 64, "STDT", backup, add_leading=True)

        def read_data_robot(self, filename):
            """
            Robot backup depends whether the robot has a linear track,
            and also on its arm configuration, so these parameters need to be saved
            """
            # If no x-axis, the XAX1 parameter becomes shorter
            xaxis = int(self.send_and_read(f"{self.read_name()}.DEQU.GTDT[18]").split(':')[1])
            logger.debug(f"XAXIS: {xaxis}")
            if xaxis == 0:
                XAX1_list = [0,1,2,3]
            else:
                XAX1_list = [0,1,2,3,8,9,10,11,12,13,14,15,16,17,18,19,40]

            arm_config = self.send_and_read(f"{self.read_name()}.DEQU.GTDT[16]")
            logger.debug(f"arm_config: {arm_config}, Type: {type(arm_config)}")
            arm_config = int(arm_config.split(":")[1])
            logger.debug(f"arm_config after changes: {arm_config}")
            arm1 = hex(arm_config)[-4:-2]
            arm2 = hex(arm_config)[-6:-4]
            logger.debug(f"arm config: {arm1}, {arm2}")

            with open(f"{filename}", "x") as backup:
                read_ip_prefix(self, backup)
                read_block(self,"DEQU", 1, "STDT", backup)
                read_block(self,"DRES", 1, "STDT", backup)
                read_block(self,"DRCI", 5, "STDT", backup)
                read_block(self,"DRCS", 5, "STDT", backup)
                read_block(self,"DRCH", 5, "STDT", backup)
                read_block(self,"DMNT", 5, "STDT", backup)
                read_block(self,"XAX1", XAX1_list, "STDT", backup)
                read_block(self,"XAX1", 1, "SPRM", backup)
                read_block(self,"ZAX1", 4, "STDT", backup)
                read_block(self,"ZAX1", 1, "SPRM", backup)
                read_block(self,"ROT1", 4, "STDT", backup)
                read_block(self,"ROT1", 1, "SPRM", backup)
                read_block(self,"ARM1", 4, "STDT", backup)
                read_block(self,"ARM1", 1, "SPRM", backup)
                read_block(self,"ARM2", 4, "STDT", backup)
                read_block(self,"ARM2", 1, "SPRM", backup)
                read_block(self,"XAX1", 16, "SEPM", backup)
                read_block(self,"ZAX1", 16, "SEPM", backup)
                read_block(self,"ROT1", 16, "SEPM", backup)
                read_block(self,"ARM1", 16, "SEPM", backup)
                read_block(self,"ARM2", 16, "SEPM", backup)
                read_block(self,"DAPM", 3, "STDT", backup)
                read_block(self,"DITK", 32, "STDT", backup)
                read_block(self,"DOUT", 32, "STDT", backup)
                read_block(self,"DTRB", 400, "STDA", backup)
                read_block(self,"DTUL", 400, "STDA", backup)
                read_block(self,"DMPR", 400, "STDT", backup)
                read_block(self,"DCFG", 400, "STDT", backup)
                for i in range(4):
                    read_block(self, "DAXM", 400, f"STDT[{i}]", backup)
                read_block(self,"DSSC", 32, "STDT", backup)
                read_block(self,"DIND", 4, "STDT", backup)
                # If Framed arm is present, read DALN
                if any(arm == "25" for arm in [arm1, arm2]):
                    read_block(self,"DALN", 32, "STDT", backup)

        # Timestamp
        ts = datetime.now().strftime("%Y%m%d")
        index = 1
        backup_dir = self.get_backup_dir()
        filename_file = f"{self.identifier[:5]}_{self.sn}_{ts}_{index}{suffix}.dat"
        filename = backup_dir / filename_file

        # Make sure to not overwrite a previous backup
        while os.path.exists(filename):
            index+=1
            filename_short = f"{self.identifier[:5]}_{self.sn}_{ts}_{index}{suffix}.dat"
            filename = backup_dir / filename_short
            logger.warning(f"File exists! Changing filename to {filename}")

        #logger.debug(f"cwd = {os.getcwd()}")
        logger.debug(f"writing backup to = {os.path.abspath(filename)}")

        # Save log level and set to INFO to avoid hundreds of debug msgs
        log_level = logging.getLogger(__name__).level
        logging.getLogger(__name__).setLevel(logging.INFO)

        try: 
            if self.identifier in LOADPORTS:
                logger.info(f"Starting Loadport Backup for {self.name}.")
                read_data_loadport(self, filename)
            elif self.identifier in ROBOTS:
                logger.info(f"Starting Robot Backup for {self.name}")
                read_data_robot(self, filename)
            elif self.identifier in PREALIGNERS:
                logger.info(f"Starting Prealigner Backup for {self.name}")
                read_data_prealigner(self, filename)
            elif self.identifier == "RTS13":
                logger.info(f"Starting Linear Track Backup for {self.name}")
                read_data_lineartrack(self, filename)
            else:
                error = f"Backup not implemented for component {self.identifier}"
                logger.error(error)
                raise Exception(error)
            status = f"Backup saved to '{filename}'"
            self.status = status
            logger.info(status)
        except Exception as e:
            logger.error(f"Reading failed: {e}")
            self.status = {f"Reading failed: {e}"}

        # restore log level
        logging.getLogger(__name__).setLevel(log_level)