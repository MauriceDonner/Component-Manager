"""
Interface module.

Contains main classes and objects for the CLI interface

If replacing this with a Flask application:

    $ make init

and then choose `flask` as template.
"""

import curses

class Menu:
    def __init__(self, components: list):
        self.xelements = 2
        self.yelements = 2
        self.button_list = components
        components.append('Configure All')
        components.append('Quit')

    def run(self,stdscr):
        # Disable cursor and enable keypad
        curses.curs_set(0)
        stdscr.keypad(1)
        stdscr.clear()

        # Menu options
        menu = self.button_list
        current_row = 0
        selected_option = None

        def draw_menu():
            stdscr.clear()
            for i, row in enumerate(menu):
                if i == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(i + 2, 2, row)
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(i + 2, 2, row)
            stdscr.refresh()

        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        while True:
            draw_menu()
            key = stdscr.getch()

            if key == curses.KEY_UP:
                current_row = (current_row - 1) % len(menu)
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(menu)
            elif key == ord('\n'):  # Enter key
                selected_option = menu[current_row]
                if selected_option == 'Quit':
                    break
                else:
                    stdscr.addstr(len(menu) + 3, 2, f"You selected: {selected_option}")
                    stdscr.refresh()
                    stdscr.getch()

        # Close curses screen
        stdscr.clear()
        stdscr.addstr(2, 2, f"Exiting. Last selected: {selected_option}")
        stdscr.refresh()
        stdscr.getch()