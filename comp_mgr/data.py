"""
Data Module

All data during commissioning is stored in these class instances
"""
from comp_mgr.variables import NETWORK

class Component:
    def __init__(self, name, system, type):
        self.name = name
        self.ip = NETWORK[system][type]
        self.system = system
        self.type = type

        # Check, whether the component has a default IP
        if self.type in NETWORK["UNCONF"].keys():
            self.defaultip = NETWORK["UNCONF"][self.type]
        elif "Loadport" in self.type:
            self.defaultip = NETWORK["UNCONF"]["Rorze LP"]
