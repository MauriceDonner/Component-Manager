"""
CLI interface for Component Manager project.
"""
import curses
import logging
import os
import sys
import threading
import time
from comp_mgr.comp_if import CompIF
from comp_mgr.comp import *
from comp_mgr.ui.testing_menu import TestingMenu
from comp_mgr.ui.component_menu import ComponentMenu
from comp_mgr.ui.autosetup_menu import AutosetupMenu

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/component_manager.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class Menu:

    def __init__(self, ip_list: list):
        self.ip_list = ip_list.copy()
        self.buttons = {ip: "[...loading]" for ip in ip_list}
        self.status = ""
        self.status_until = 0
        logger.info(40 * "=" + " PROGRAM START" + 40 * "=")
        for i in ip_list:
            logger.info(f"Found IP: {i}")
    
    def set_status(self, message, duration=3):
        self.status_message = message
        self.status_until = time.time() + duration

    def draw_status_popup(self, stdscr):
        if time.time() >= self.status_until:
            return
        
        height, width = stdscr.getmaxyx()
        msg = self.status_message
        box_width = len(msg) + 4
        box_height = 3

        start_y = 0
        start_x = (width - box_width) // 2

        stdscr.attron(curses.A_BLINK)
        stdscr.addstr(start_y, start_x, "+" + "-" * (box_width - 2) + "+")
        stdscr.addstr(start_y + 1, start_x, "| " + msg + " |")
        stdscr.addstr(start_y + 2, start_x, "+" + "-" * (box_width - 2) + "+")
        stdscr.attroff(curses.A_BLINK)

    def init_button_list(self):
        self.button_list = self.ip_list.copy()
        self.button_list.append('Testing')
        self.button_list.append('Retry connection')
        if len(self.ip_list) >= 2:
            self.button_list.append('Configure all unconfigured')
        self.button_list.append('Quit')

    def update_main_buttons(self) -> None:
        """Get component information from each ip address and update the displayed text"""
        comp_if = CompIF()
        all_components = {}
        threads = []

        def update_button(ip: str) -> None:
            comp_info = comp_if.get_component_info(ip)
            all_components[ip] = comp_info
            system = comp_info['System']
            type = comp_info['Type']
            name = comp_info['Name']
            sn = comp_info['SN']
            firmware = comp_info['Firmware']
            if name:
                info = f"{system} {type} {name} {sn} v{firmware}"
            # If no name is assigned - show which system the ip is configured for
            elif system:
                info = f"{system} {type}"
            # If no system is assigned - only show component type
            elif type:
                info = type
            else:
                info = "[unidentified]"
            self.buttons[ip] = info

        for ip in self.ip_list:
            thread = threading.Thread(target=update_button, args=(ip,),daemon=True)
            threads.append(thread)
            thread.start()
            # update_button(ip)

        # Wait for all threads to finish before returning
        for t in threads:
            t.join()
        
        logger.debug('=== ALL COMPONENTS ===')
        for ip in self.ip_list:
            logger.debug(f'{all_components[ip]}')

        return all_components
        

    def draw_main_menu(self, stdscr, current_row):
        stdscr.clear()
        for i, row in enumerate(self.button_list):
            display_text = row
            if row in self.buttons:
                display_text += f" → {self.buttons[row]}"
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 2, display_text[:curses.COLS - 4])
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 2, 2, display_text[:curses.COLS - 4])

        self.draw_status_popup(stdscr)

        stdscr.refresh()

    def run_main_menu(self, stdscr):
        self.init_button_list()
        curses.curs_set(0) # Disable cursor and enable keypad
        stdscr.keypad(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        current_row = 0
        stdscr.timeout(500)

        threading.Thread(target=self.update_main_buttons, daemon=True).start()

        while True:
            self.draw_main_menu(stdscr, current_row)
            key = stdscr.getch()
            if key == curses.KEY_UP:
                current_row = (current_row - 1) % len(self.button_list)
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(self.button_list)
            elif key == ord('\n'):  # Enter key
                selected = self.button_list[current_row]
                if selected == 'Quit':
                    sys.exit(0)
                elif selected == 'Testing':
                    TestingMenu().run(stdscr)
                elif selected == 'Retry connection':
                    stdscr.addstr(len(self.button_list) + 3, 2, f"Scanning for components...")
                    stdscr.refresh()
                    comp_if = CompIF()
                    self.ip_list = comp_if.discover()
                    self.buttons = {ip: "[...loading]" for ip in self.ip_list}
                    self.init_button_list()
                    threading.Thread(target=self.update_main_buttons, daemon=True).start()
                elif self.buttons[selected] == "[...loading]":
                    message = "Please wait, until the component is connected"
                    self.set_status(message, 3)
                elif self.buttons[selected] == "Configure all unconfigured":
                    AutosetupMenu.run(stdscr, self.ip_list)
                    message = "Please wait, until the component is connected"
                    self.set_status(message, 3)
                else:
                    comp_if = CompIF()
                    comp_info = comp_if.get_component_info(selected)
                    ComponentMenu(comp_info).run(stdscr)
                    current_row = 0 # After returning, select current row

def main():
    """
    The main function executes on commands:
    `python -m comp_mgr`
    Program's entry point.
    """
    logging.getLogger(__name__)
    Components = CompIF(debug=1)
    ip_list = Components.discover()
    menu = Menu(ip_list)
    curses.wrapper(menu.run_main_menu)
