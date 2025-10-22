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
        """
        self.stdscr = stdscr
        self.title = title
        self.options = options
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
            key = opt["key"]
            val = self.config.get(key, False) # Returns `False` if key doesn't exist
            typ = opt["type"]

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
            pass
        self.config[key] = new_val

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
                if selected["type"] == "checkbox":
                    current_val = self.config.get(selected["key"], False)
                    self.config[selected["key"]] = not current_val
                elif selected["type"] == "value":
                    self.edit_value(win, selected["key"])
                elif selected["type"] == "selection":
                    self.config[selected["key"]] = selected["label"]
                    break
            elif key == 27:  # ESC to exit
                break

        del win  # Cleanup window