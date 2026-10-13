import curses
import time
import logging
import sys

logger = logging.getLogger(__name__)

def draw_status_popup(stdscr, msg: str, until):
    """Draw a temporary popup box centered at the bottom of the screen."""
    if not msg or time.time() >= until:
        return
    
    height, width = stdscr.getmaxyx()
    box_width = len(msg) + 4

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
    def __init__(self, stdscr, title, config):
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
        self.config = config
        self.items = list(config.values()) + [{'label': 'Back'}]
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
        for i, cfg in enumerate(self.items):
            label = cfg["label"]
            typ = cfg.get("type", None)
            
            if typ == "checkbox":
                display = f"[{'X' if cfg['enabled'] else ' '}] {label}"
            elif typ == "value":
                display = f"{label}: {cfg.get('value','')}"
            elif typ == "selection":
                display = f"-> {label}"
            elif typ == "sub_selection":
                display = f"{label}: {cfg.get('value','')}"
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
        try:
            if new_val == '':
                self.config[key]['value'] = None
                self.config[key]['enabled'] = False
            else:
                self.config[key]['value'] = new_val
                self.config[key]['enabled'] = True
        except Exception as e:
            logger.error(e)
            sys.exit(0)

    def run(self):
        """Run the popup"""
        height, width = self.stdscr.getmaxyx()
        win_height = len(self.items) + 6
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
                self.current_row = (self.current_row - 1) % len(self.items)
            elif key == curses.KEY_DOWN:
                self.current_row = (self.current_row + 1) % len(self.items)
            elif key == ord("\n"):
                selected = self.items[self.current_row]
                label = selected.get("label", None)
                type = selected.get("type", None)
                config_entry = selected.get("key", None)
                if type == "checkbox":
                    current_val = self.config[config_entry]['enabled']
                    self.config[config_entry]['enabled'] = not current_val
                elif type == "value":
                    self.current_row+=1
                    self.edit_value(win, config_entry)
                elif type == "selection":
                    return label
                elif type == 'sub_selection':
                    current_row_tmp = self.current_row
                    initial = self.config[config_entry]['value']
                    new_value = self.draw_subwindow(label, selected['options'])
                    if new_value != initial:
                        self.config[config_entry]['enabled'] = True
                    else:
                        self.config[config_entry]['enabled'] = False
                    self.config[config_entry]['value'] = new_value
                    self.current_row = current_row_tmp
                elif type == "confirmation":
                    return self.config
                else:
                    break
            elif key == 27:  # ESC to exit
                break

        del win  # Cleanup window

class ConfirmationPopup:
    def __init__(self, stdscr, title, lines):
        """
        :param stdscr: curses main window
        :param title: str – popup title
        :param lines: list[dict] – lines to display
        Example:
           [{"text": "Are you sure?", "align": "center"},
            {"text": "This will modify the configuration.", "align": "left"},
            {"text": "The change cannot be undone.", "align": "center"}]
        """
        self.stdscr = stdscr
        self.title = title
        self.lines = lines
        self.current_button = 0

        self.buttons = ["Confirm", "Reject"]

    def draw(self, win):
        """Draw the popup."""
        win.clear()
        win.box()

        height, width = win.getmaxyx()

        # Title
        win.attron(curses.A_BOLD)
        win.addstr(0, 2, f" {self.title} ")
        win.attroff(curses.A_BOLD)

        # Draw text lines
        for i, line in enumerate(self.lines):
            text = line.get("text", "")
            alignment = line.get("align", "left")

            # Don't let text overwrite the box borders
            available_width = width - 4
            text = text[:available_width]

            if alignment == "center":
                x = (width - len(text)) // 2
            else:
                x = 2

            try:
                win.addstr(i + 2, x, text)
            except curses.error:
                pass

        # Buttons
        button_y = height - 2

        confirm = "[ Confirm ]"
        reject = "[ Reject ]"

        total_width = len(confirm) + len(reject) + 6
        start_x = (width - total_width) // 2

        confirm_x = start_x
        reject_x = confirm_x + len(confirm) + 6

        if self.current_button == 0:
            win.attron(curses.color_pair(1))
            win.addstr(button_y, confirm_x, confirm)
            win.attroff(curses.color_pair(1))
            win.addstr(button_y, reject_x, reject)
        else:
            win.addstr(button_y, confirm_x, confirm)
            win.attron(curses.color_pair(1))
            win.addstr(button_y, reject_x, reject)
            win.attroff(curses.color_pair(1))

        win.refresh()

    def run(self):
        """Run the confirmation popup and return the selected button."""
        height, width = self.stdscr.getmaxyx()

        # +6 gives room for:
        # top border
        # title
        # spacing
        # text
        # buttons
        # bottom border
        win_height = len(self.lines) + 6

        # Make popup wide enough for both buttons and the longest line
        longest_line = max(
            [len(str(line.get("text", ""))) for line in self.lines],
            default=0
        )

        button_width = len("[ Confirm ]") + len("[ Reject ]") + 6

        win_width = max(
            width // 2,
            longest_line + 4,
            button_width + 4
        )

        # Don't make popup larger than terminal
        win_width = min(win_width, width - 2)
        win_height = min(win_height, height - 2)

        start_y = (height - win_height) // 2
        start_x = (width - win_width) // 2

        win = curses.newwin(
            win_height,
            win_width,
            start_y,
            start_x
        )

        win.keypad(True)

        curses.start_color()
        curses.init_pair(
            1,
            curses.COLOR_BLACK,
            curses.COLOR_WHITE
        )

        while True:
            self.draw(win)

            key = win.getch()

            if key in (curses.KEY_LEFT, curses.KEY_UP):
                self.current_button = 0

            elif key in (curses.KEY_RIGHT, curses.KEY_DOWN):
                self.current_button = 1

            elif key in (ord("\n"), curses.KEY_ENTER):
                return self.buttons[self.current_button]

            elif key == 27:  # ESC
                return "Reject"

        del win

class PopupInput:
    def __init__(self, stdscr, title, text):
        self.stdscr = stdscr
        self.title = title
        self.text = text
        self.input = None
    
    def draw(self):
        height, width = self.stdscr.getmaxyx()
        win_height = 4
        win_width = width // 2
        text_length = len(self.text)
        start_y = (height - win_height ) // 2
        start_x = (width - win_width) // 2

        win = curses.newwin(win_height, win_width, start_y, start_x)
        win.keypad(True)

        win.clear()
        win.box()

        win.attron(curses.A_BOLD)
        win.addstr(0,2,f" {self.title} ")
        win.attroff(curses.A_BOLD)

        win.addstr(win_height - 2,2,f"{self.text} ")

        curses.echo()
        new_val = win.getstr(win_height - 2, text_length + 2, 20).decode("utf-8")
        curses.noecho()
        if new_val == '':
            return "" 
        else:
            logger.debug(f"value received: {new_val}")
            return new_val

class ScrollingLog:
    def __init__(self, stdscr, max_lines=1000):
        self.buffer = []
        self.max_lines = max_lines
        self.stdscr = stdscr

    def add(self, line: str, start_y=1, start_x=1, height=None, width=None):
        """Add a new line to the log"""
        self.buffer.append(line)

        # Prevent unlimited growth
        if len(self.buffer) > self.max_lines:
            self.buffer.pop(0)

        """Draw visible portion of log to screen"""
        if height is None or width is None:
            h, w = self.stdscr.getmaxyx()
            height = h - start_y
            width = w - start_x
        
        self.stdscr.clear()

        # Only display last visible lines
        visible_lines = self.buffer[-height:]

        for i, line in enumerate(visible_lines):
            try:
                self.stdscr.addstr(start_y + i, start_x, line[:width])
            except curses.error:
                pass  # Prevent crash on edge cases
        
        self.stdscr.refresh()