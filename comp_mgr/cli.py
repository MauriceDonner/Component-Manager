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
from comp_mgr.exceptions import *
from comp_mgr.ui import TestingMenu, ComponentMenu, AutosetupMenu
from comp_mgr.ui.common_ui import draw_status_popup

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
        self.status_message = None
        self.status_until = 0
        logger.info(40 * "=" + " PROGRAM START" + 40 * "=")
        for i in ip_list:
            logger.info(f"Found IP: {i}")

    def init_button_list(self):
        self.button_list = self.ip_list.copy()
        self.button_list.append('Testing')
        self.button_list.append('Retry connection')
        # if len(self.ip_list) >= 2:
        self.button_list.append('Configure all unconfigured')
        self.button_list.append('Quit')

    
    def set_status(self, message, duration=3):
        self.status_message = message
        self.status_until = time.time() + duration

    def update_main_buttons(self) -> None:
        """Get component information from each ip address and update the displayed text"""
        comp_if = CompIF()
        self.all_components = {}

        def update_button(ip: str) -> None:
            comp_info = comp_if.get_component_info(ip)
            self.all_components[ip] = comp_info
            system = comp_info['System']
            type = comp_info['Type']
            name = comp_info['Name']
            sn = comp_info['SN']
            firmware = comp_info['Firmware']

            # Information Cascade - Reduce infomation if not available
            if firmware:
                info = f"{system} {type} {name} {sn} v{firmware}"
            elif name:
                info = f"{system} {type} {name} {sn}"
            elif system:
                info = f"{system} {type}"
            elif type:
                info = type
            else:
                info = "[unidentified]"
            self.buttons[ip] = info

        for ip in self.ip_list:
            threading.Thread(target=update_button, args=(ip,),daemon=True).start()

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

        draw_status_popup(stdscr, self.status_message, self.status_until)

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
                elif selected == "[...loading]":
                    self.set_status("Please wait, until the component is connected", 3)
                elif selected == "Configure all unconfigured":
                    if any(info == '[...loading]' for info in self.buttons.values()):
                        self.set_status("Please wait, until all components are connected", 3)
                    else:
                        try:
                            AutosetupMenu(self.ip_list, self.all_components).run(stdscr)
                        except DoubleConfiguration as e:
                            self.set_status(str(e), 3)
                        except TestException as e:
                            self.set_status(str(e), 3)
                        except Exception as e:
                            self.set_status(str(e), 3)
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
    Components = CompIF()
    ip_list = Components.discover()
    menu = Menu(ip_list)
    curses.wrapper(menu.run_main_menu)
