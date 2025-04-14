"""CLI interface for project_name project.

Be creative! do whatever you want!

- Install click or typer and create a CLI app
- Use builtin argparse
- Start a web application
- Import things from your .base module
"""

# TODO: Organize requirements and installations properly
import curses
from comp_mgr.interface import Menu

def main():
    """
    The main function executes on commands:
    `python -m project_name` and `$ project_name `.

    Program's entry point.
    """

    # TODO: Function that detects any component according to Network variable
    components = ["RA_420","RR_757", "LP1", "LP2"]

    menu = Menu(components)
    curses.wrapper(menu.run)
    print("Program ran successfully")
