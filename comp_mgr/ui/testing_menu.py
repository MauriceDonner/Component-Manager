import curses
import logging
import sys

from comp_mgr.ui.common_ui import *
# from comp_mgr.cli.component_menu import ComponentMenu
# from comp_mgr.cli.common_ui import draw_status_popup

logger = logging.getLogger(__name__)

class TestingMenu:

    def __init__(self):
        self.tests = {
            "hello_world": self.hello_world,
            "update_center_popup": self.update_center_popup,
            "Back": None,
            "Quit": None
        }

    def draw(self, stdscr, current_row):
        stdscr.clear()
        stdscr.addstr(0,0,"Testing area, proceed with caution!")
        test_names = list(self.tests.keys())
        for i, name in enumerate(test_names):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 4, name)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 2, 4, name)
        stdscr.refresh()

    def run(self, stdscr):
        test_names = list(self.tests.keys())
        current_row = 0
        while True:
            self.draw(stdscr, current_row)
            key = stdscr.getch()
            if key == curses.KEY_UP:
                current_row = (current_row - 1) % len(test_names)
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(test_names)
            elif key == ord('\n'):
                selected = test_names[current_row]
                if selected == 'Back':
                    break
                elif selected == 'Quit':
                    sys.exit(0)
                else:
                    action = self.tests[selected]
                    response = action(stdscr)
                    if response:
                        height, width = stdscr.getmaxyx()
                        textpos = int(width/2)-int(len(response)/2)
                        stdscr.attron(curses.A_BLINK)
                        stdscr.addstr(height-1,textpos,response)
                        stdscr.refresh()
                        stdscr.getch()
                        stdscr.attroff(curses.A_BLINK)

    def hello_world(self, stdscr):
        logger.info("Hello World")
        return "Hello World"

    def update_center_popup(self, stdscr):
        options = {
            'x_offset_upper':   {"label": "X Offset upper  ", "type": "value", "value": 0, "key": "x_offset_upper"},
            'y_offset_upper':   {"label": "Y Offset upper  ", "type": "value", "value": 0, "key": "y_offset_upper"},
            'x_offset_lower':   {"label": "X Offset lower  ", "type": "value", "value": 0, "key": "x_offset_lower"},
            'y_offset_lower':   {"label": "Y Offset lower  ", "type": "value", "value": 0, "key": "y_offset_lower"},
            'x_offset_flipped': {"label": "X Offset flipped", "type": "value", "value": 0, "key": "x_offset_flipped"},
            'y_offset_flipped': {"label": "Y Offset flipped", "type": "value", "value": 0, "key": "y_offset_flipped"},
            'confirm': {"label": "Confirm", "type": "confirmation", "key": "confirm"}
        }
        popup = PopupMenu(stdscr, "Adjust wafer centering", options)
    
        setting = popup.run()

        logger.debug("Centering update:")
        for coord in setting.values():
            if coord['label'] == 'Confirm': continue
            logger.debug(f"{coord['label']}: {coord['value']}")
        
        logger.info("Adjusting centering values...")

        lines = [
        {"text": "Please confirm the following action:", "align": "center"},
        {"text": "The wafer centering values will be updated.", "align": "left"},
        {"text": "This cannot be undone.", "align": "center"},
        ]
        popup = ConfirmationPopup(stdscr, "Confirm update", lines)
        result = popup.run()

        if result == "Confirm":
            logger.debug("Confirm")
        elif result == "Reject":
            logger.debug("Reject")

        sys.exit(0)
        # component.update_center(setting) #TODO write component function