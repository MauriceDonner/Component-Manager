"""
Main component interface module.

Contains classes and functions for component communication
"""

import concurrent.futures
import socket
import subprocess
import sys
from comp_mgr.variables import NETWORK
from comp_mgr.data import Component

class CompIF:

    def __init__(self):
        self.status = "OK"
        self.system = "UNCONF"

    # Ping function for windows (doesnt work on linux)
    def ping(self,ip):
        command = ["ping", "-n", "1", "-w", "1000", ip]  # 500ms timeout
        result = subprocess.run(command, stdout=subprocess.DEVNULL)
        return ip if result.returncode == 0 else None

    def establish_connection(self,ip,port=12100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((ip,port))

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
        
        # Components are stored in a dictionary and are instances off the data.Component class
        Clist = {}
        for system in NETWORK:
            for entry in NETWORK[system]:
                if NETWORK[system][entry] in alive:
                    name = f"{entry}_{system}"
                    Clist[name] = Component(name,system,entry)

        return Clist