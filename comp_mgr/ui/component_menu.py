import curses, sys, threading, time
import ipaddress
import logging
from comp_mgr.ui.common_ui import draw_status_popup, PopupInput
from comp_mgr.comp import Rorze
from comp_mgr.config import COMPONENT_MENU_OPTIONS

logger = logging.getLogger(__name__)

class ComponentMenu:
    def __init__(self, comp_info: dict):
        self.comp_info = comp_info
        self.component = None
        self.status_message = ""
        self.status_until = 0
        self.menu_actions = []

    def _resolve_action_entry(self, entry: dict) -> dict:
        """
        Convert config entry string into a callable in comp.py or here
        """
        resolved = entry.copy()

        # Resolve an action
        action_name = entry.get('action')
        def action_callable(component, fn=action_name):
            method = getattr(component, fn, None) # component.fn
            if not callable(method):
                self.set_status(f'Action not implemented', 3)
                return
            return method()
        resolved['action'] = action_callable
        
        # Resolve an action factory (in the case of a ui menu)
        factory_name = entry.get('action_factory')
        if isinstance(factory_name, str):
            factory_method = getattr(self, factory_name, None)
            if not callable(factory_method):
                resolved['action_factory'] = lambda stdscr: (lambda c: self.set_status("Factory not implemented", 3))
            else:
                resolved['action_factory'] = lambda stdscr, fm=factory_method: fm(stdscr)
        
        return resolved

    def set_status(self, msg, duration=3):
        self.status_message = msg
        self.status_until = time.time() + duration

    #TODO draw menu options only when component is not busy
    def draw(self, stdscr, current_row, labels):
        c = self.component
        stdscr.clear()

        stdscr.addstr(1, 0, f"Component: {c.display_name} {c.identifier} v{c.firmware}")
        stdscr.addstr(2, 0, f"Current IP: {c.ip}")
        stdscr.addstr(3, 0, f"System: {c.system}")
        stdscr.addstr(4, 0, f"Status: {c.status}")

        if c.busy:
            stdscr.addstr(1, 50, "=== BUSY ===")

        for i, label in enumerate(labels):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 6, 5, label)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 6, 5, label)

        draw_status_popup(stdscr, self.status_message, self.status_until)
        stdscr.refresh()

    def build_menu(self):
        """Build menu from COMPONENT_MENU_OPTIONS"""
        identifier = self.comp_info["Identifier"]
        raw = []

        raw.extend(COMPONENT_MENU_OPTIONS.get("Common", []))
        raw.extend(COMPONENT_MENU_OPTIONS.get(identifier, []))

        self.menu_actions = [self._resolve_action_entry(e) for e in raw]

    def run_action(self, action):
        if self.component.busy:
            self.set_status("Component busy", 2)
            return

        fn = action.get("action")
        if not callable(fn):
            self.set_status("Action not implemented", 3)
            return

        threading.Thread(target=fn, args=(self.component,),daemon=True).start()

    def run_action_factory(self, stdscr, action):
        if self.component.busy:
            self.set_status("Component busy", 2)
            return
        
        factory = action.get("action_factory")
        if not callable(factory):
            self.set_status("Action not implemented", 3)
            return

        fn = factory(stdscr)
        if not callable(fn):
            self.set_status("Action not implemented", 3)
            return
        
        fn(self.component)
    
    def change_host_popup(self,stdscr):
        def _action(component):
            current = component.get_host_IP()
            ip = PopupInput(stdscr, f"Set Host IP Address ({current})", "Enter IP address: ").draw()
            try:
                iptest = ipaddress.IPv4Address(ip)
                component.set_host_IP(ip)
            except ipaddress.AddressValueError:
                logger.error(f"ValueError in ip address. Expected 4 octets in {ip}")
                self.set_status(f"IP address parsing error. Expected 4 octets in {ip}")
        return _action

    def change_port_popup(self, stdscr):
        def _action(component):
            current = component.get_host_port()
            port = PopupInput(stdscr, f"Set TCP/IP Port ({current})", "Enter Port number: ").draw()
            try:
                port_int = int(port)
            except:
                logger.error(f"Value error in port: Value is not a valid number (0-65535)")
                self.set_status(f"The entered value is not a valid number (0-65535)")
                return
            if 0 <= port_int < 65536:
                component.set_host_port(port)
            else:
                logger.error(f"Value error in port: Value exceeds the port limit (0-65535)")
                self.set_status(f"Port parsing error. Port exceeds limit (0-65535)")
        return _action

    def change_log_host_popup(self, stdscr):
        def _action(component):
            current = component.get_log_host()
            ip = PopupInput(stdscr, f"Set IP address of the log host ({current})", "Enter IP address: ").draw()
            try:
                iptest = ipaddress.IPv4Address(ip)
                component.set_log_host(ip)
            except ipaddress.AddressValueError:
                logger.error(f"ValueError in ip address. Expected 4 octets in {ip}")
                self.set_status(f"IP address parsing error. Expected 4 octets in {ip}")
        return _action
    
    def change_IP_popup(self, stdscr):
        def _action(component):
            ip = PopupInput(stdscr, "Change component IP", "Enter IP address: ").draw()
            try:
                iptest = ipaddress.IPv4Address(ip)
                component.change_IP(ip)
            except ipaddress.AddressValueError:
                logger.error(f"ValueError in ip address. Expected 4 octets in {ip}")
                self.set_status(f"IP address parsing error. Expected 4 octets in {ip}")
        return _action
    
    def run(self, stdscr):
        name = self.comp_info["Name"]
        if any(p in name for p in ["TRB", "ALN", "STG", "TBL", "SIM"]):
            self.component = Rorze(self.comp_info)
        else:
            raise Exception("Unsupported component type")

        self.build_menu()

        default_items = ["Back", "Quit"]
        labels = [a["label"] for a in self.menu_actions] + default_items

        curses.curs_set(0)
        stdscr.keypad(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        stdscr.timeout(500)

        current_row = 0

        while True:
            self.draw(stdscr, current_row, labels)
            key = stdscr.getch()

            if key == -1:
                continue

            elif key == curses.KEY_UP:
                current_row = (current_row - 1) % len(labels)

            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(labels)

            elif key == ord("\n"):
                selected = labels[current_row]

                if selected == "Back":
                    break
                elif selected == "Quit":
                    sys.exit(0)
                elif 'action_factory' in self.menu_actions[current_row]:
                    action_entry = self.menu_actions[current_row]
                    self.run_action_factory(stdscr, action_entry)
                else:
                    action = self.menu_actions[current_row]
                    self.run_action(action)