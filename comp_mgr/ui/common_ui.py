import curses
import time

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
