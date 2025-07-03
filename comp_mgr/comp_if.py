"""
Main interface between software and component.

Contains utility classes and functions
"""

import concurrent.futures
import logging
import subprocess
import json # Debugging
from comp_mgr.config import NETWORK
from comp_mgr.comp import Component

logger = logging.getLogger(__name__)

class CompIF:

    def __init__(self,debug=0):
        self.status = "OK"
        self.system = "UNCONF"
        self.debug = debug

        # TODO testing
        self.connection_threads = []

    # Ping function for windows (doesnt work on linux)
    def ping(self,ip):
        command = ["ping", "-n", "1", "-w", "1000", ip]  # 500ms timeout
        result = subprocess.run(command, stdout=subprocess.DEVNULL)
        return ip if result.returncode == 0 else None

    # Check which type of component is connected
    def check_component_type(comp_info):
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
            logger.info(f"Component type detected: Rorze")
            return component.type
        else:
            logger.error(f"Unknown Component type {component.type}")
            raise Exception(f"Unkown Component type {component.type}")

    # Discover all components in the relevant sub nets
    def discover(self):
        """Ping all known component IPs and find every component that is connected"""

        ips = [ip for system in NETWORK.values() for ip in system.values()]

        alive = []

        # Choose system preset
        if any(ip.startswith('192.168.0.') for ip in alive):
            self.system = "SEMDEX" 
        elif any(ip.startswith('192.168.30.') for ip in alive):
            if self.system == "SEMDEX":
                raise Exception("Both SemDex and WMC configurations found!")
            self.system = "WMC"

        n_workers = len(ips)
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
            results = executor.map(self.ping, ips)
            for result in results:
                if result:
                    alive.append(result)
        
        # Component data is stored in a dictionary and are instances off the data.Component class
        Clist = {}
        for system in NETWORK:
            for entry in NETWORK[system]:
                if NETWORK[system][entry] in alive:
                    name = f"{entry}_{system}"
                    Clist[name] = {}
                    Clist[name]["system"] = system
                    Clist[name]["type"] = entry
                    Clist[name]["IP"] = NETWORK[system][entry]

        if self.debug:
            with open('testing/Component_List_Dict.json', 'w') as out:
                json.dump(Clist, out)

        return Clist