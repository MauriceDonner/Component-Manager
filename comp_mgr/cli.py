"""
CLI interface for Component Manager project.
"""
import curses
import sys
import threading
from comp_mgr.config import MESSAGES
from comp_mgr.methods import CompIF
from comp_mgr.comp import Component
from testing.methods import tests

class Menu:

    def __init__(self, clist: dict):
        self.components = clist

    def init_button_list(self):
        self.button_list = []
        for i in self.components.keys():
            button = self.components[i]["IP"]+" "+i
            self.button_list.append(button)
        # self.button_list.append('Configure all unconfigured')
        self.button_list.append('Testing')
        self.button_list.append('Retry connection')
        self.button_list.append('Quit')

    def draw_main_menu(self, stdscr, current_row):
        stdscr.clear()
        self.init_button_list()
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
                elif selected == 'Configure all unconfigured':
                    stdscr.addstr(len(self.button_list) + 3, 2, f"Configuration starts...")
                    stdscr.refresh()
                    stdscr.getch()
                elif selected == 'Testing':
                    self.run_testing_menu(stdscr, tests(stdscr))
                elif selected == 'Retry connection':
                    stdscr.addstr(len(self.button_list) + 3, 2, f"Scanning for components...")
                    stdscr.refresh()
                    comp_if = CompIF()
                    self.components = comp_if.discover()
                    self.init_button_list()
                else:
                    component = self.components[selected.split(" ")[1]]
                    self.run_component_menu(stdscr,component)
                    # After returning, select current row
                    current_row = 0

    def draw_component_menu(self, stdscr, component: Component, current_row, button_list):
        stdscr.clear()
        stdscr.addstr(0,0,component.type)
        stdscr.addstr(1,0,f"Current IP: {component.ip}")
        stdscr.addstr(2,0,f"System: {component.system}")
        stdscr.addstr(3,0,f"Status: {component.status}")
        for i, row in enumerate(button_list):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 5, 5, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 5, 5, row)
        stdscr.refresh()

    def run_component_menu(self, stdscr, comp_info: dict):

        # Instantiate Component
        component = Component(
            ip = comp_info["IP"],
            system = comp_info["system"],
            type = comp_info["type"]
        )

        def update_status():
            try:
                component.establish_connection()
            except Exception as e:
                component.status = f"Error: {e}"
        
        connection_thread = threading.Thread(target=update_status, daemon=True)
        connection_thread.start()

        # Start Menu at the same time (update every 500ms)
        button_list = ["Origin", "Back", "Quit"]
        current_row = 0
        stdscr.timeout(1000)

        while True:
            self.draw_component_menu(stdscr, component, current_row, button_list)
            key = stdscr.getch()
            if key == -1:
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
                elif selected == 'Origin':
                    connection_thread = threading.Thread(target=component.origin_search, daemon=True)
                    connection_thread.start()


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
    clist = Components.discover()

    # TODO testing, what argument goes here?
    # Components.start_background_connections()

    menu = Menu(clist)
    curses.wrapper(menu.run_main_menu)