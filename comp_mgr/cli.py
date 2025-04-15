"""
CLI interface for project_name project.

Be creative! do whatever you want!

- Install click or typer and create a CLI app
- Use builtin argparse
- Start a web application
- Import things from your .base module
"""
import curses
from comp_mgr.comp_if import CompIF
from comp_mgr.data import Component

# TODO: Organize requirements and installations properly

class Menu:

    def __init__(self, components: dict):
        self.ncolumns = 2
        self.current_row = 0
        self.components = components
        self.button_list = list(components.keys())
        self.selected_option = None

        self.button_list.append('Configure All Unconfigured')
        self.button_list.append('Quit')

    def draw_menu(self, stdscr):
        menu = self.button_list
        stdscr.clear()
        for i, row in enumerate(menu):
            if i == self.current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 2, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 2, 2, row)
        stdscr.refresh()

    def draw_component_menu(self, stdscr, Component):
        stdscr.clear()
        stdscr.addstr(0,0,Component.name)
        stdscr.addstr(1,0,f"Current IP: {Component.ip}")
        stdscr.addstr(2,0,f"Status: {Component.system}")
        component_menu = ["Back","Quit"]
        self.current_row = 3
        for i, row in enumerate(component_menu):
            if i == self.current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 3, 2, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 3, 2, row)
        stdscr.refresh()
        # Menu of the single component. Should show the component name, currenty IP, status
        # and also the configuration applied. Goal IP (SemDex or WMC or custom), checkboxes
        # for checklist items

    def run(self,stdscr):
        # Disable cursor and enable keypad
        curses.curs_set(0)
        stdscr.keypad(1)
        stdscr.clear()

        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        menu = self.button_list

        while True:
            self.draw_menu(stdscr)
            key = stdscr.getch()

            if key == curses.KEY_UP:
                self.current_row = (self.current_row - 1) % len(menu)
            elif key == curses.KEY_DOWN:
                self.current_row = (self.current_row + 1) % len(menu)
            elif key == ord('\n'):  # Enter key
                selected_option = menu[self.current_row]
                if selected_option == 'Quit':
                    break
                if selected_option == 'Configure All':
                    stdscr.addstr(len(menu) + 3, 2, f"Configuration starts...")
                    stdscr.refresh()
                    stdscr.getch()
                if selected_option == 'Back':
                    self.draw_menu(stdscr)
                    stdscr.refresh()
                    stdscr.refresh()
                else:
                    component = self.components[selected_option]
                    self.draw_component_menu(stdscr,component)
                    stdscr.addstr(len(menu) + 3, 2, f"You selected: {component}")
                    stdscr.refresh()
                    stdscr.getch()

        # Close curses screen
        stdscr.clear()
        stdscr.addstr(2, 2, f"Exiting. Last selected: {selected_option}")
        stdscr.refresh()
        stdscr.getch()

def main():
    """
    The main function executes on commands:
    `python -m project_name` and `$ project_name `.

    Program's entry point.
    """

    # TODO: Function that detects any component according to Network variable

    Components = CompIF()
    clist = Components.discover()
    #clist = ["Robot, IP: 192.168.0.1, Status: SEMDEX"]

    menu = Menu(clist)
    curses.wrapper(menu.run)
    print("Program ran successfully")