import curses, sys, threading, time
import logging
from comp_mgr.ui.common_ui import draw_status_popup
from comp_mgr.comp import Rorze

logger = logging.getLogger(__name__)

class ComponentMenu:
    def __init__(self, comp_info: dict):
        self.comp_info = comp_info
        self.component = None
        self.status_message = ""
        self.status_until = 0

    def set_status(self, msg, duration=3):
        self.status_message = msg
        self.status_until = time.time()+duration

    def draw(self, stdscr, current_row, button_list):
        c = self.component 
        stdscr.clear()
        stdscr.addstr(1,0,f'Component: {c.display_name} {c.ctype} v{c.firmware}')
        stdscr.addstr(2,0,f"Current IP: {c.ip}")
        stdscr.addstr(3,0,f"System: {c.system}")
        stdscr.addstr(4,0,f"Status: {c.status}")

        if c.busy:
            stdscr.addstr(1,50,f'=== BUSY ===')

        for i, row in enumerate(button_list):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 6, 5, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 6, 5, row)

        draw_status_popup(stdscr, self.status_message, self.status_until)
        stdscr.refresh()

    def run(self, stdscr):
        """
        Takes the component information and creates a detailed status page by communicating with the component
        comp_info = {'IP': '192.168.0.1', 'System': 'SEMDEX', 'Type': 'Robot', 'Name': 'TRB1', 'SN': 'XXXXX', etc.}
        """
        comp_info = self.comp_info

        type = comp_info["Type"]
        name = comp_info["Name"]

        if type == 'Simulation':
                name = 'Simulation'

        if any(p in name for p in ['TRB','ALN','STG','TBL','Simulation']):
            # Instantiate a Rorze component 
            self.component = Rorze(comp_info)
        else:
            raise Exception("Other components than Rorze have not been implemented yet")

        button_list_limited = ["Back", "Quit"]
        buttons = ["Get Status", "Read Data", "Rotary Switch"]
        button_list = buttons + button_list_limited
        current_row = 0
        stdscr.timeout(500)

        while True:
            self.draw(stdscr, current_row, button_list)
            key = stdscr.getch()

            if key == -1:
                button_list = button_list_limited if self.component.busy else buttons + button_list_limited
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
                    threading.Thread(target=self.component.get_status, daemon=True).start()
                elif selected == 'Origin':
                    threading.Thread(target=self.component.origin_search, daemon=True).start()
                elif selected == 'Read Data':
                    threading.Thread(target=self.component.read_data, daemon=True).start()
                elif selected == 'Rotary Switch':
                    threading.Thread(target=self.component.get_rotary_switch_value, daemon=True).start()

            # Also update button list right after a command is started
            button_list = button_list_limited if self.component.busy else buttons + button_list_limited