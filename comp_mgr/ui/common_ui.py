import curses
import time
import logging

logger = logging.getLogger(__name__)

def draw_status_popup(stdscr, msg: str, until):
    """Draw a temporary popup box centered at the bottom of the screen."""
    if not msg or time.time() >= until:
        return
    
    height, width = stdscr.getmaxyx()
    box_width = len(msg) + 4
    box_height = 3

    start_y = 0
    start_x = (width - box_width) // 2

    try:
        stdscr.attron(curses.A_BLINK)
        stdscr.addstr(start_y, start_x, "+" + "-" * (box_width - 2) + "+")
        stdscr.addstr(start_y + 1, start_x, "| " + msg + " |")
        stdscr.addstr(start_y + 2, start_x, "+" + "-" * (box_width - 2) + "+")
        stdscr.attroff(curses.A_BLINK)
    except curses.error:
        pass # Ignore if terminal is too small

class PopupMenu:
    def __init__(self, stdscr, title, options, config):
        """
        :param stdscr: curses main window
        :param title: str – window title
        :param options: list[dict] – menu options
                        Each dict can contain:
                          {"label": "Enable feature", "type": "checkbox", "key": "feature_enabled"}
                          {"label": "Timeout (s)", "type": "value", "key": "timeout"}
        :param config: dict – shared config dict that will be updated by the popup
                        Example: all_components[0]['Config_List']]
        """
        self.stdscr = stdscr
        self.title = title
        self.options = options + [{'label': 'Back'}]
        self.config = config
        self.current_row = 0

    def draw_window(self, win):
        """Draws the popup content"""
        win.clear()
        height, width = win.getmaxyx()
        win.box()

        # Title
        win.attron(curses.A_BOLD)
        win.addstr(0, 2, f" {self.title} ")
        win.attroff(curses.A_BOLD)

        # Draw all options
        for i, opt in enumerate(self.options):
            label = opt["label"]
            key = opt.get("key", None)
            val = self.config.get(key, False)
            typ = opt.get("type", None)

            if typ == "checkbox":
                display = f"[{'X' if val else ' '}] {label}"
            elif typ == "value":
                display = f"{label}: {val}"
            elif typ == "selection":
                display = f"-> {label}"
            else:
                display = label

            if i == self.current_row:
                win.attron(curses.color_pair(1))
                win.addstr(i + 2, 2, display[:width - 4])
                win.attroff(curses.color_pair(1))
            else:
                win.addstr(i + 2, 2, display[:width - 4])

        win.refresh()

    def draw_subwindow(self, title, options):
        """Draws a smaller popup subwindow in which a selection can be made"""
        self.current_row = 0
        height, width = self.stdscr.getmaxyx()
        win_height = len(options)+4
        win_width = max(len(title),max(len(str(option)) for option in options))+4
        start_y = (height - win_height) // 2
        start_x = (width - win_width) // 2

        win = curses.newwin(win_height, win_width, start_y, start_x)
        win.keypad(True)

        while True:
            win.clear()
            win.box()
            # Title
            win.attron(curses.A_BOLD)
            win.addstr(0, 2, f" {title} ")
            win.attroff(curses.A_BOLD)

            # Draw all options from the list
            for i, opt in enumerate(options):
                display = f"-> {opt}"

                if i == self.current_row:
                    win.attron(curses.color_pair(1))
                    win.addstr(i + 2, 2, display[:width - 4])
                    win.attroff(curses.color_pair(1))
                else:
                    win.addstr(i + 2, 2, display[:width - 4])

            win.refresh()

            key = win.getch()
            if key == curses.KEY_UP:
                self.current_row = (self.current_row - 1) % len(options)
            elif key == curses.KEY_DOWN:
                self.current_row = (self.current_row + 1) % len(options)
            elif key == ord("\n"):
                selected = options[self.current_row]
                return selected
            elif key == 27:  # ESC to exit
                break

    def edit_value(self, win, key):
        """Prompt the user to enter a new value"""
        height, width = win.getmaxyx()
        win.addstr(height - 2, 2, "Enter new value: ")
        curses.echo()
        new_val = win.getstr(height - 2, 20, 20).decode("utf-8")
        curses.noecho()
        try:
            new_val = int(new_val) if new_val.isdigit() else new_val
        except ValueError:
            logger.warning(f"ValueError in common_ui -> edit_value: '{new_val}' not parsed correctly")
            pass
        self.config[key]['value'] = new_val

    def run(self):
        """Run the popup"""
        height, width = self.stdscr.getmaxyx()
        win_height = len(self.options) + 6
        win_width = width // 2
        start_y = (height - win_height) // 2
        start_x = (width - win_width) // 2

        win = curses.newwin(win_height, win_width, start_y, start_x)
        win.keypad(True)

        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        while True:
            self.draw_window(win)
            key = win.getch()

            if key == curses.KEY_UP:
                self.current_row = (self.current_row - 1) % len(self.options)
            elif key == curses.KEY_DOWN:
                self.current_row = (self.current_row + 1) % len(self.options)
            elif key == ord("\n"):
                selected = self.options[self.current_row]
                label = selected.get("label", None)
                type = selected.get("type", None)
                config_entry = selected.get("key", None)
                if type == "checkbox":
                    current_val = self.config[config_entry]['enabled']
                    self.config[config_entry]['enabled'] = not current_val
                elif type == "value":
                    self.edit_value(win, config_entry)
                elif type == "selection":
                    self.config[config_entry] = label
                    break
                elif type == 'sub_selection':
                    current_row_tmp = self.current_row
                    value = self.draw_subwindow(label, selected['options'])
                    self.config[config_entry]['value'] = value
                    self.current_row = current_row_tmp
                else:
                    break
            elif key == 27:  # ESC to exit
                break

        del win  # Cleanup window