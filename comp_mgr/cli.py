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
from testing.methods import tests

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
        self.button_list.append('Quit')

    def update_main_buttons(self) -> None:
        """Get component information from each ip address and update the displayed text"""
        comp_if = CompIF()

        def update_button(ip: str) -> None:
            # try:
            component_info = comp_if.get_component_info(ip)
            system = component_info['System']
            type = component_info['Type']
            name = component_info['Name']
            sn = component_info['SN']
            if name:
                info = f"{system} {type} {name} {sn}"
            # If no name is assigned - show which system the ip is configured for
            elif system:
                info = f"{system} {type}"
            # If no system is assigned - only show component type
            elif type:
                info = type
            else:
                info = "[unidentified]"
            self.buttons[ip] = info
            # except Exception as e:
            #     self.buttons[ip] = f"[error: {e}]"

        for ip in self.ip_list:
            # thread = threading.thread(target=update_button, args=(ip,),daemon=True).start()
            update_button(ip)

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
                    self.run_testing_menu(stdscr, tests(stdscr))
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
                else:
                    comp_if = CompIF()
                    comp_info = comp_if.get_component_info(selected)
                    self.run_component_menu(stdscr, comp_info)
                    current_row = 0 # After returning, select current row

    def draw_component_menu(self, stdscr, component: Component, current_row, button_list):
        stdscr.clear()
        stdscr.addstr(0,0,f'Component: {component.display_name}')
        stdscr.addstr(1,0,f"Current IP: {component.ip}")
        stdscr.addstr(2,0,f"System: {component.system}")
        stdscr.addstr(3,0,f"Status: {component.status}")

        if component.busy:
            stdscr.addstr(0,50,f'=== BUSY ===')

        for i, row in enumerate(button_list):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 5, 5, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 5, 5, row)
        stdscr.refresh()

    def run_component_menu(self, stdscr, comp_info: dict):
        """
        Takes the component information and creates a detailed status page by communicating with the component
        comp_info = {'IP': '192.168.0.1', 'System': 'SEMDEX', 'Type': 'Robot', 'Name': 'TRB1', 'SN': 'XXXXX'}
        """

        ip = comp_info["IP"]
        system = comp_info["System"]
        type = comp_info["Type"]
        name = comp_info["Name"]

        if type == 'Simulation':
                name = 'Simulation'

        if any(p in name for p in ['TRB','ALN','STG','TBL','Simulation']):
            # Instantiate a Rorze component 
            component = Rorze(comp_info)
        else:
            raise Exception("Other components than Rorze have not been implemented yet")

        button_list_limited = ["Back", "Quit"]
        buttons = ["Get Status", "Read Data", "Rotary Switch"]
        button_list = buttons + button_list_limited
        current_row = 0
        stdscr.timeout(500)

        while True:
            self.draw_component_menu(stdscr, component, current_row, button_list)
            key = stdscr.getch()
            if key == -1:
                button_list = button_list_limited if component.busy else buttons + button_list_limited
                continue
            elif key == curses.KEY_UP:
                current_row = (current_row - 1) % len(button_list)
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(button_list)
            elif key == ord('\n'):
                selected = button_list[current_row]
                if selected == 'Back':
                    break
                elif selected == 'Quit':
                    sys.exit(0)
                elif selected == 'Get Status':
                    threading.Thread(target=component.get_status, daemon=True).start()
                elif selected == 'Origin':
                    threading.Thread(target=component.origin_search, daemon=True).start()
                elif selected == 'Read Data':
                    threading.Thread(target=component.read_data, daemon=True).start()
                elif selected == 'Rotary Switch':
                    threading.Thread(target=component.get_rotary_switch_value, daemon=True).start()

            # Also update button list right after a command is started
            button_list = button_list_limited if component.busy else buttons + button_list_limited

    def draw_testing_menu(self, stdscr, current_row, button_list):
        stdscr.clear()
        stdscr.addstr(0,0,f"Testing area, proceed with caution!")
        for i, row in enumerate(button_list):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 4, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 2, 4, row)
        stdscr.refresh()

    def run_testing_menu(self, stdscr, tests):
        button_list = tests.button_list
        current_row = 0
        while True:
            self.draw_testing_menu(stdscr, current_row, button_list)
            key = stdscr.getch()
            if key == curses.KEY_UP:
                current_row = (current_row - 1) % len(button_list)
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(button_list)
            elif key == ord('\n'):
                selected = button_list[current_row]
                if selected == 'Back':
                    break
                elif selected == 'Quit':
                    sys.exit(0)
                else:
                    response = tests.respond(selected)
                    height, width = stdscr.getmaxyx()
                    textpos = int(width/2)-int(len(response)/2)
                    stdscr.attron(curses.A_BLINK)
                    stdscr.addstr(height-1,textpos,response)
                    stdscr.refresh()
                    stdscr.getch()
                    stdscr.attroff(curses.A_BLINK)

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
