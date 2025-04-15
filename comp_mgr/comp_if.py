"""
Main component interface module.

Contains classes and functions for component communication
"""

import os
from comp_mgr.variables import NETWORK
from comp_mgr.data import Component

class CompIF:

    def __init__(self):
        self.status = "OK"
        self.system = "UNCONF"

    # Discover all components in a network
    def discover(self):
        """Ping all known component IPs and find every component that is connected"""

        # Components are stored in a dictionary and are instances off the data.Component class
        Clist = {}

        # Define ping parameter (-n for windows, -c for linux)
        ntries = 1
        timeout = 1 # in seconds
        ocount = f"-n {ntries}" if os.sys.platform.lower()=="win32" else f"-c {ntries}"
        otimeout = f"-w {int(1000*timeout)}" if os.sys.platform.lower()=="win32" else f"-W {timeout}"

        # Loop through all default IPs 
        for system in NETWORK:
            for entry in NETWORK[system]:

                ip = NETWORK[system][entry]
                status = f"{system}"

                # Check for component response
                response = os.system(f"ping {ocount} {otimeout} {ip}")
                if response == 0:
                    # Create a Component instance in the Component list
                    name = f"{entry}_{system}"
                    Clist[name] = Component(name,system,entry)

                    if (self.system != "UNCONF") and (system != self.system):
                        raise Exception("Both SemDex and WMC configurations found!")

                    # Remember, which system is being configured
                    self.system = {system}

        return Clist 