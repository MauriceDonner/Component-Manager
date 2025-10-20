
import curses, sys
from testing.methods import tests

# from comp_mgr.cli.component_menu import ComponentMenu
# from comp_mgr.cli.common_ui import draw_status_popup

class TestingMenu:

    def __init__(self):
        self.tests = tests(None)

    def draw(self, stdscr, current_row):
        stdscr.clear()
        stdscr.addstr(0,0,f"Testing area, proceed with caution!")
        for i, row in enumerate(self.tests.button_list):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 4, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 2, 4, row)
        stdscr.refresh()

    def run(self, stdscr):
        button_list = self.tests.button_list
        current_row = 0
        while True:
            self.draw(stdscr, current_row)
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
                    response = self.tests.respond(selected)
                    height, width = stdscr.getmaxyx()
                    textpos = int(width/2)-int(len(response)/2)
                    stdscr.attron(curses.A_BLINK)
                    stdscr.addstr(height-1,textpos,response)
                    stdscr.refresh()
                    stdscr.getch()
                    stdscr.attroff(curses.A_BLINK)