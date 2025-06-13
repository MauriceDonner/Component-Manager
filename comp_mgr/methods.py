"""
Main functional module.

Contains utility classes and functions
"""

import concurrent.futures
import subprocess
import threading
from comp_mgr.config import NETWORK
from comp_mgr.comp import Component

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

    # TODO testing
    def start_background_connections(self, component_list: list):
        for component in component_list:
            ip = component.ip
            t = threading.Thread(target=self.establish_connection(ip), args=(ip),daemon=True)
            t.start()
            self.connection_threads.append(t)

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
                    Clist[name] = Component(name,system,entry)

        return Clist