"""
Main interface between software and component.

Contains utility classes and functions
"""

import concurrent.futures
import logging
import socket
import subprocess
import time
from comp_mgr.config import NETWORK, OTHER_IPS
from comp_mgr.comp import Component

logger = logging.getLogger(__name__)

class CompIF:

    def __init__(self):
        self.status = "OK"
        self.system = "UNCONF"

        # TODO testing
        self.connection_threads = []

    # Ping function for windows (doesnt work on linux)
    def ping(self,ip):
        command = ["ping", "-n", "1", "-w", "1000", ip]  # 500ms timeout
        result = subprocess.run(command, stdout=subprocess.DEVNULL)
        return ip if result.returncode == 0 else None

    # Discover all alive ips in the relevant sub nets
    def discover(self):
        """Ping all known component IPs and find every component that is connected"""

        ips = [ip for system in NETWORK.values() for ip in system.values()]
        ips+=list(OTHER_IPS.keys())

        alive = []

        n_workers = len(ips)
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
            results = executor.map(self.ping, ips)
            for result in results:
                if result:
                    alive.append(result)

        # Choose system preset
        if any(ip.startswith('192.168.0.') for ip in alive):
            self.system = "SEMDEX" 
        elif any(ip.startswith('192.168.30.') for ip in alive):
            if self.system == "SEMDEX":
                raise Exception("Both SemDex and WMC configurations found!")
            self.system = "WMC"

        return alive

    # Check which type of component is connected
    def check_component_type(comp_info: dict):
        component = Component(
            ip = comp_info["IP"],
            system = comp_info["system"],
            type = comp_info["type"]
        )

        try:
            component.establish_connection() # Modifies its type
        except Exception as e:
            logger.error(f"Failed to establish connection to Component {component.type}")
            raise Exception(f"Failed to establish connection to Component {component.type}: {e}")
            
        # If rorze component is connected use a diffent class
        if any(p in component.type for p in ['TRB','ALN','STG']):
            logger.info(f"Component type detected: Rorze ({component.type})")
            return component.type
        else:
            logger.error(f"Unknown Component type {component.type}")
            raise Exception(f"Unkown Component type {component.type}")

    def send_and_read_rorze(self, sock: socket.socket, command: str, buffer: int=1024) -> str:

        # Add a \r at the end of a command!
        command = f"{command}\r"

        logger.debug(f"Sending: {command}")
        sock.sendall(command.encode('utf-8')) 
        try: 
            read = sock.recv(buffer)
            logger.debug(f"Receive: {read}")
            message = str(read)[2:-3].split(':')[1]
        except socket.timeout:
            logger.error(f"Timeout")
        except socket.error as e:
            logger.error(f"Socket error: {e}")
        except Exception as e:
            logger.warning(f"Weird message received: {read}")
            return str(read)

        return message

    def get_ip_info(self, target_ip: str) -> str:
        """Check whether the IP corresponds to an actual component"""
        for system, components in NETWORK.items():
            for component, ip in components.items():
                if ip == target_ip:
                    ip_info = {"IP": ip, "System": system, "Type": component}
                    logger.info(f"Received ip info: {ip_info}")
                    return ip_info
        for ip, description in OTHER_IPS.items():
            if ip == target_ip:
                ip_info = {"IP": ip, "System": None, "Type": description}
                logger.info(f"Received ip info: {ip_info}")
                return ip_info
        
        ip_info = {"IP": ip, "System": None, "Type": "Unknown IP"}
        logger.info(f"Received ip info: {ip_info}")
        return ip_info

    def get_component_info(self, ip: str, port:int=12100) -> dict:
        """
        Creates the comp_info dictionary. This is unified for all components, regardless of manufacturer:
        {'IP':       192.168.0.1,
         'System':   SEMDEX,
         'Type':     Robot,
         'Name':     TRB1,
         'SN'        XXXXX
         'CType':    RR757
         'Firmware': 1.19U
        }
        """
        # Check, whether the ip corresponds to an actual component
        comp_info = self.get_ip_info(ip)

        if comp_info["Type"] == "Unknown IP":
            comp_info["Name"] = None
            comp_info["SN"] = None
            comp_info["CType"] = None
            comp_info["Firmware"] = None
            logger.debug(f"Received component info: {comp_info}")
            return comp_info

        if comp_info["Type"] == "Simulation":
            comp_info["Name"] = 'SIM1'
            comp_info["SN"] = 'SIM1234'
            comp_info["CType"] = 'SIM_COMPONENT'
            comp_info["Firmware"] = '1.19U'
            return comp_info

        # TODO: Add check, whether it can be connected to (aka only connect to robot, PA, or Loadport)

        # If its a component, find out which type
        logger.info(f"Connecting to {ip}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        retries = 0

        for i in range(retries+1):

            try:
                sock.connect((ip, port))
                read = str(sock.recv(1024))
                logger.debug(f"Recieved: {read} from {ip}")
                message = read[2:-3] # Cuts the b' and \\r

                # If Rorze component, return name and serial number
                if any(p in read for p in ['TRB','ALN','STG','TBL']):
                    logger.debug("Component type detected: Rorze")
                    name = message.split('.')[0][1:]
                    logger.debug(f"Short name: {name}")
                    # Get Rorze Serial Number
                    sn_command = f"o{name}.DEQU.GTDT[0]"
                    serial_number = self.send_and_read_rorze(sock,sn_command)
                    # Get Rorze Component Type and Firmware version
                    verstring = self.send_and_read_rorze(sock, f"o{name}.GVER").split(" ")
                    ctype, firmware, = verstring[-4], verstring[-2]
                    comp_info["Name"] = name
                    comp_info["SN"] = serial_number.split('"')[1]
                    comp_info["CType"] = ctype
                    comp_info["Firmware"] = firmware
                    logger.info(f"Received component info: {comp_info}")
                    return comp_info

                else: # TODO Add more components here
                    comp_info["Name"] = None
                    comp_info["SN"] = None
                    comp_info["CType"] = None
                    comp_info["Firmware"] = None
                    logger.info(f"Received component info: {comp_info}")
                    return comp_info

            except socket.timeout:
                logger.warning(f"Connection Timeout when connecting to {ip}... Retrying {retries-i} more times.")
                time.sleep(1)
            except socket.error as e:
                logger.warning(f"Connection attempt to {ip} unsuccessful... Retrying {retries-i} more times.")
                time.sleep(1)

        # If no connection can be established, return empty info
        comp_info["Name"] = None
        comp_info["SN"] = None
        comp_info["CType"] = None
        comp_info["Firmware"] = None
        logger.info(f"Received component info: {comp_info}")
        return comp_info