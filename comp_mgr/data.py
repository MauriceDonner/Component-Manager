"""
Data Module

All data during commissioning is stored in these class instances
"""
from comp_mgr.variables import NETWORK

class Component:
    def __init__(self, system, type):
        self.type = type
        self.ip = NETWORK[system][type]

        # Check, whether the component has a default IP
        if self.type in NETWORK["DEFAULT"].keys():
            self.defaultip = NETWORK["DEFAULT"][self.type]
        elif "Loadport" in self.type:
            self.defaultip = NETWORK["DEFAULT"]["Rorze LP"]
