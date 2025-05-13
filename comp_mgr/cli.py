"""
CLI interface for Component Manager project.
"""
import curses
from comp_mgr.comp_if import CompIF
from comp_mgr.data import Component
from testing.methods import tests

# TODO: Organize requirements and installations properly

class Menu:

    def __init__(self, components: dict):
        self.components = components
        self.button_list = list(components.keys())
        self.button_list.append('Configure all unconfigured')
        self.button_list.append('Testing')
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

    def draw_component_menu(self, stdscr, component: Component, current_row, button_list):
        stdscr.clear()
        stdscr.addstr(0,0,component.name)
        stdscr.addstr(1,0,f"Current IP: {component.ip}")
        stdscr.addstr(2,0,f"Status: {component.system}")
        for i, row in enumerate(button_list):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 4, 4, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 4, 4, row)
        stdscr.refresh()

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

    def run_main_menu(self,stdscr):
        # Disable cursor and enable keypad
        curses.curs_set(0)
        stdscr.keypad(True)
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
                    break
                if selected == 'Configure all unconfigured':
                    stdscr.addstr(len(self.button_list) + 3, 2, f"Configuration starts...")
                    stdscr.refresh()
                    stdscr.getch()
                if selected == 'Testing':
                    self.run_testing_menu(stdscr, tests(stdscr))
                else:
                    component = self.components[selected]
                    self.run_component_menu(stdscr,component)
                    # After returning, select current row
                    current_row = 0
    
    def run_component_menu(self, stdscr, component: Component):
        button_list = ["Back", "Quit"]
        current_row = 0
        while True:
            self.draw_component_menu(stdscr, component, current_row, button_list)
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
                    exit(0)

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
                    exit(0)
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

    Components = CompIF()
    clist = Components.discover()

    menu = Menu(clist)
    curses.wrapper(menu.run_main_menu)
    print("Program ran successfully")