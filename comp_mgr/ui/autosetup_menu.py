import curses
import logging
from comp_mgr.comp_if import CompIF
from comp_mgr.exceptions import TestException, DoubleConfiguration

logger = logging.getLogger(__name__)

class AutosetupMenu:

    def __init__(self, ip_list, all_components):
        self.ip_list = ip_list
        self.all_components = all_components
        self.system = None

        logger.debug('=== ALL COMPONENTS ===')
        for ip in self.ip_list:
            logger.debug(f'{self.all_components[ip]}')
        
        # Check whether to setup for SemDex or WMC ip space
        if any(ip.startswith('192.168.0.') for ip in ip_list):
            self.system = "SEMDEX"
        elif any(ip.startswith('192.168.30.') for ip in ip_list):
            if self.system == "SEMDEX":
                logger.error("Both WMC and SemDex configurations found!")
                raise DoubleConfiguration("Both WMC and SemDex configurations found!")
            self.system = "WMC"

    def run(self, stdscr):
        a = 5
        if a == 5: raise TestException("This is a test exception")