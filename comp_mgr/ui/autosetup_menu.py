import curses
import logging
import sys
import time
from comp_mgr.comp_if import CompIF
from comp_mgr.exceptions import TestException, DoubleConfiguration
from comp_mgr.ui.common_ui import PopupMenu, draw_status_popup

logger = logging.getLogger(__name__)

class AutosetupMenu:
    def __init__(self, ip_list, all_components):
        self.ip_list = ip_list
        self.all_components = all_components
        self.button_list = ["Test Popup", "Choose system", "Back", "Quit"]
        self.system = None
        # Create a main config object in which EVERYTHING is saved
        self.config = {"system": self.system}
        self.status_message = ""
        self.status_until = 0

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
    
    def set_status(self, msg, duration=3):
        self.status_message = msg
        self.status_until = time.time() + duration

    def draw(self, stdscr, current_row):
        stdscr.addstr(0,0,f"Config: {self.config}")
        for i, row in enumerate(self.button_list):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 4, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 2, 4, row)

        draw_status_popup(stdscr, self.status_message, self.status_until)
        stdscr.refresh()

    def choose_system(self, stdscr):
        options = [
            {"label": "WMC", "type": "selection", "key": "system"},
            {"label": "SEMDEX", "type": "selection", "key": "system"}
        ]
        popup = PopupMenu(stdscr, "Choose System", options, self.config)
        popup.run()

        stdscr.clear()
        stdscr.refresh()

    def run(self, stdscr):
        button_list = self.button_list
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        current_row = 0
        stdscr.timeout(500)

        if self.system == None:
            self.choose_system(stdscr)

        while True:
            stdscr.clear()
            self.draw(stdscr, current_row)
            key = stdscr.getch()
            if key == curses.KEY_UP:
                current_row = (current_row - 1) % len(button_list)
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(button_list)
            elif key == ord('\n'):
                selected = button_list[current_row]
                if selected == 'Test Popup': 
                    self.set_status("POPUP TEST", 3)
                    stdscr.refresh()
                if selected == 'Choose system':
                    self.choose_system(stdscr)
                if selected == 'Back':
                    break
                elif selected == 'Quit':
                    sys.exit(0)
            
        a = 5
        if a == 5: raise TestException("This is a test exception")