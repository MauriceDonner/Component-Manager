"""
CLI interface for Component Manager project.
"""
import curses
import logging
import os
import sys
import threading
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
        self.ip_list = ip_list
        logger.info("==================== PROGRAM START ====================")

    def init_button_list(self):
        self.button_list = self.ip_list
        # self.button_list.append('Configure all unconfigured') # Zukunftsmusik
        self.button_list.append('Testing')
        self.button_list.append('Retry connection')
        self.button_list.append('Quit')

    def draw_main_menu(self, stdscr, current_row):
        stdscr.clear()
        for i, row in enumerate(self.button_list):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 2, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 2, 2, row)
        stdscr.refresh()

    def run_main_menu(self,stdscr):

        self.init_button_list()

        # Disable cursor and enable keypad
        curses.curs_set(0)
        stdscr.keypad(True)
        # Choose Colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        current_row = 0
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
                    self.init_button_list()
                else:
                    comp_info = self.buttons[selected.split(" ")[1]]
                    self.run_component_menu(stdscr,comp_info)
                    # After returning, select current row
                    current_row = 0

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

        # Check component type (to validate if IP matches expected component)
        comp_type = CompIF.check_component_type(comp_info)
        logger.debug(f"component.type={comp_type}")

        if not any(p in comp_type for p in ['TRB','ALN','STG']):
            raise Exception("Other components than Rorze have not been implemented yet")

        # Instantiate a Rorze component 
        component = Rorze(
            ip = comp_info["IP"],
            system = comp_info["system"],
            type = comp_type
        )

        # Start thread that updates component status in the background            
        def update_status():
            try:
                component.establish_connection()
            except Exception as e:
                component.status = f'Error: {e}'

        connection_thread = threading.Thread(target=update_status, daemon=True)
        connection_thread.start()

        # Start Menu (update every 500ms)
        button_list_limited = ["Back", "Quit"]
        buttons = ["Get Status", "Read Data", "Rotary Switch"]
        button_list = buttons + button_list_limited
        current_row = 0
        stdscr.timeout(500)

        while True:

            self.draw_component_menu(stdscr, component, current_row, button_list)

            key = stdscr.getch()
            if key == -1:
                # Update button list and continue
                if component.busy:
                    button_list = button_list_limited
                else: 
                    button_list = buttons + button_list_limited
                continue
            elif key == curses.KEY_UP:
                current_row = (current_row - 1) % len(button_list)
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(button_list)
            elif key == ord('\n'):  # Enter key
                selected = button_list[current_row]
                if selected == 'Back':
                    break
                elif selected == 'Quit':
                    sys.exit(0)
                elif selected == 'Get Status':
                    connection_thread = threading.Thread(target=component.get_status, daemon=True)
                    connection_thread.start()
                elif selected == 'Origin':
                    connection_thread = threading.Thread(target=component.origin_search, daemon=True)
                    connection_thread.start()
                elif selected == 'Read Data':
                    connection_thread = threading.Thread(target=component.acquire_system_data, daemon=True)
                    connection_thread.start()
                elif selected == 'Rotary Switch':
                    connection_thread = threading.Thread(target=component.get_rotary_switch_value, daemon=True)
                    connection_thread.start()

            # Also update button list right after a command is started
            if component.busy:
                button_list = button_list_limited
            else: 
                button_list = buttons + button_list_limited


    def draw_testing_menu(self, stdscr, current_row, button_list):
        stdscr.clear()
        stdscr.addstr(0,0,f"Testing area, proceed with caution!")
        self.init_button_list()
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
            elif key == ord('\n'):  # Enter key
                selected = button_list[current_row]
                if selected == 'Back':
                    break
                elif selected == 'Quit':
                    sys.exit(0)
                else:
                    tests.respond(selected)
                    stdscr.refresh()
                    stdscr.getch()

def main():
    """
    The main function executes on commands:
    `python -m comp_mgr`
    Program's entry point.
    """

    Components = CompIF(debug=1)
    ip_list = Components.discover()

    # TODO testing, what argument goes here?
    # Components.start_background_connections()

    menu = Menu(ip_list)
    curses.wrapper(menu.run_main_menu)