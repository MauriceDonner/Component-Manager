import curses, sys, threading, time
import ipaddress
import logging
from comp_mgr.ui.common_ui import *
from comp_mgr.comp import Rorze
from comp_mgr.config import COMPONENT_MENU_OPTIONS
from comp_mgr.exceptions import *

logger = logging.getLogger(__name__)

class ComponentMenu:
    def __init__(self, comp_info: dict, simulation: bool):
        self.comp_info = comp_info
        self.component = None
        self.status_message = ""
        self.status_until = 0
        self.menu_actions = []
        self.simulation = simulation

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
                self.set_status('Action not implemented', 3)
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

    # TODO draw menu options only when component is not busy (should function - test this)
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
                # Test whether ip is correct (throws exception if not)
                ipaddress.IPv4Address(ip)
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
                logger.error("Value error in port: Value is not a valid number (0-65535)")
                self.set_status("The entered value is not a valid number (0-65535)")
                return
            if 0 <= port_int < 65536:
                component.set_host_port(port)
            else:
                logger.error("Value error in port: Value exceeds the port limit (0-65535)")
                self.set_status("Port parsing error. Port exceeds limit (0-65535)")
        return _action

    def upper_laser_popup(self, stdscr):
        def _action(component):
            options = {
                'on': {"label": "on", "type": "selection", "key": "on"},
                'off': {"label": "off", "type": "selection", "key": "off"}
            }
            popup = PopupMenu(stdscr, "Set upper laser", options)
            setting = popup.run()
            if setting: 
                component.set_laser('upper', setting)
        return _action

    def lower_laser_popup(self, stdscr):
        def _action(component):
            options = {
                'on': {"label": "on", "type": "selection", "key": "on"},
                'off': {"label": "off", "type": "selection", "key": "off"}
            }
            popup = PopupMenu(stdscr, "Set lower laser", options)
            setting = popup.run()
            if setting: 
                component.set_laser('lower', setting)
        return _action

    def change_log_host_popup(self, stdscr):
        def _action(component):
            current = component.get_log_host()
            ip = PopupInput(stdscr, f"Set IP address of the log host ({current})", "Enter IP address: ").draw()
            try:
                # Test whether ip is correct (throws exception if not)
                ipaddress.IPv4Address(ip)
                component.set_log_host(ip)
            except ipaddress.AddressValueError:
                logger.error(f"ValueError in ip address. Expected 4 octets in {ip}")
                self.set_status(f"IP address parsing error. Expected 4 octets in {ip}")
        return _action
    
    def change_IP_popup(self, stdscr):
        def _action(component):
            ip = PopupInput(stdscr, "Change component IP", "Enter IP address: ").draw()
            try:
                # Test whether ip is correct (throws exception if not)
                ipaddress.IPv4Address(ip)
                component.change_IP(ip)
            except ipaddress.AddressValueError:
                logger.error(f"ValueError in ip address. Expected 4 octets in {ip}")
                self.set_status(f"IP address parsing error. Expected 4 octets in {ip}")
        return _action

    def set_speed_popup(self, stdscr):
        def _action(component):
            # Read speed from component
            name = component.read_name()
            command = f"{name}.DRCS[003].GTDT[11]"
            current_speed_value = component.send_and_read(command)
            if int(current_speed_value) == 120000:
                current_speed = "Fast"
            elif int(current_speed_value) == 30000:
                current_speed = "Slow"
            else:
                current_speed = current_speed_value
            options = {
                'Fast': {"label": "Fast", "type": "selection", "key": "Fast"},
                'Slow': {"label": "Slow", "type": "selection", "key": "Slow"}
            }
            popup = PopupMenu(stdscr, f"Set aligner speed (current speed setting: {current_speed})", options)
            setting = popup.run()
            component.set_alignment_speed(speed=setting)
        return _action
    
    def set_flip_near_popup(self, stdscr):
        def _action(component):
            options = {
                'On': {"label": "On", "type": "selection", "key": "On"},
                'Off': {"label": "Off", "type": "selection", "key": "Off"}
            }
            popup = PopupMenu(stdscr, "Set flip near", options)
            setting = popup.run()
            component.set_flip_near(setting=setting)
        return _action

    def update_center_popup(self, stdscr):
        def _action(component):
            options = {
                'x_offset_upper':   {"label": "X Offset upper  ", "type": "value", "value": 0, "key": "x_offset_upper"},
                'y_offset_upper':   {"label": "Y Offset upper  ", "type": "value", "value": 0, "key": "y_offset_upper"},
                'x_offset_lower':   {"label": "X Offset lower  ", "type": "value", "value": 0, "key": "x_offset_lower"},
                'y_offset_lower':   {"label": "Y Offset lower  ", "type": "value", "value": 0, "key": "y_offset_lower"},
                'x_offset_flipped': {"label": "X Offset flipped", "type": "value", "value": 0, "key": "x_offset_flipped"},
                'y_offset_flipped': {"label": "Y Offset flipped", "type": "value", "value": 0, "key": "y_offset_flipped"},
                'confirm': {"label": "Confirm", "type": "confirmation", "key": "confirm"}
            }
            # In case the user wants to configure a single station
            options_reduced = {
                'x_offset_upper':   {"label": "X Offset upper  ", "type": "value", "value": 0, "key": "x_offset_upper"},
                'y_offset_upper':   {"label": "Y Offset upper  ", "type": "value", "value": 0, "key": "y_offset_upper"},
                'x_offset_lower':   {"label": "X Offset lower  ", "type": "value", "value": 0, "key": "x_offset_lower"},
                'y_offset_lower':   {"label": "Y Offset lower  ", "type": "value", "value": 0, "key": "y_offset_lower"},
                'confirm': {"label": "Confirm", "type": "confirmation", "key": "confirm"}
            }

            # Let the user choose the station ID or fallback to standard station IDs
            station_id = PopupInput(stdscr,"Enter Station ID for stage teaching (leave blank if standard)", "Station ID:").draw()

            # If the standard is selected,
            if station_id == "":

                # check the default station ids first
                check_default = component.check_centering_station()
                if check_default != "Success":

                    # This means, the station teaching is not correct or the user entered the wrong id
                    station_id = PopupInput(stdscr,"WARNING: Teaching station not found. Enter station ID","Station ID:").draw()
                    try:
                        station_id_int = int(station_id)
                    except (ValueError, TypeError):
                        raise OutOfRange("Station ID must be an integer between 0 and 399")

                    # Check user station
                    if not 0 <= station_id_int < 400:
                        logger.error("Station ID out of range (0-399)")
                        raise OutOfRange("Entered station ID is out of range (0-399)")
                    check_user_station = component.check_centering_station(user_stage_id=station_id_int)
                    if check_user_station != "Success":
                        error = f"The teaching data of station {station_id_int} is out of range of the expected stage teaching (value: {check_user_station})"
                        logger.error(error)
                        raise TeachingDataOutOfRange(error)

                    # If user station fits, use reduced center teaching menu
                    popup = PopupMenu(stdscr, "Adjust wafer centering", options_reduced)

                # The data of the default teaching station fits within the expected value
                else: 
                    popup = PopupMenu(stdscr, "Adjust wafer centering", options)
                    if component.system == "WMC":
                        station_id_int = 150
                    elif component.system == "SEMDEX":
                        station_id_int = 2
            
            else: 
                # Check user station
                try:
                    station_id_int = int(station_id)
                except (ValueError, TypeError):
                    raise OutOfRange("Station ID must be an integer between 0 and 399")
                if not 0 <= station_id_int < 400:
                    logger.error("Station ID out of range (0-399)")
                    raise OutOfRange("Entered station ID is out of range (0-399)")
                check_user_station = component.check_centering_station(user_stage_id=station_id_int)
                if check_user_station != "Success":
                    error = f"The teaching data of station {station_id_int} is out of range of the expected stage teaching (value: {check_user_station})"
                    logger.error(error)
                    raise TeachingDataOutOfRange(error)
                popup = PopupMenu(stdscr, "Adjust wafer centering", options_reduced)
        
            setting = popup.run()

            # TODO For debugging
            logger.debug("Centering update:")
            for coord in setting.values():
                if coord['label'] == 'Confirm': continue
                logger.debug(f"{coord['label']}: {coord['value']}")
            
            logger.info("Acquiring teaching data...")

            teaching_values = {
                'x_offset_upper':   component.get_teaching_value(station_id_int, 0),
                'y_offset_upper':   component.get_teaching_value(station_id_int, 6),
                'x_offset_lower':   component.get_teaching_value(station_id_int, 1),
                'y_offset_lower':   component.get_teaching_value(station_id_int, 7),
                'x_offset_flipped': component.get_teaching_value(station_id_int+1, 0),
                'y_offset_flipped': component.get_teaching_value(station_id_int+1, 6),
            }

            logger.debug(f"Acquired data: {teaching_values}")
            logger.debug(f"User Input: {setting}")

            # Create a copy to alter
            updated_values = teaching_values.copy()

            # Compare each value
            lines = []
            for coord in setting.values():
                if coord['label'] == 'Confirm': continue
                coord_key = coord['key']
                original_value = teaching_values[coord_key]
                updated_values[coord_key] = original_value + int(coord['value'])
                line = f"{coord['label']}: {original_value} + {coord['value']} -> {updated_values[coord_key]}"
                lines.append({"text": line, "align": "left"})

            logger.debug(f"Updated values: {updated_values}")
            
            popup = ConfirmationPopup(stdscr, "Confirm teaching changes", lines)
            result = popup.run()

            if result == "Reject":
                error = "User rejected changing teaching values"
                logger.error(error)
                raise UserRejection(error)

            # Apply teaching
            component.set_teaching_value(station_id_int, 0, updated_values['x_offset_upper'], write=0)
            component.set_teaching_value(station_id_int, 6, updated_values['y_offset_upper'], write=0)
            component.set_teaching_value(station_id_int, 1, updated_values['x_offset_lower'], write=0)
            component.set_teaching_value(station_id_int, 7, updated_values['y_offset_lower'], write=0)
            component.set_teaching_value(station_id_int+1, 0, updated_values['x_offset_flipped'], write=0)
            component.set_teaching_value(station_id_int+1, 6, updated_values['y_offset_flipped'], write=1)

        return _action
    
    def run(self, stdscr):
        name = self.comp_info["Name"]
        if any(p in name for p in ["TRB", "ALN", "STG", "TBL"]):
            self.component = Rorze(self.comp_info, self.simulation)
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
                    self.component.close_connection()
                    break
                elif selected == "Quit":
                    sys.exit(0)
                elif 'action_factory' in self.menu_actions[current_row]:
                    action_entry = self.menu_actions[current_row]
                    try:
                        self.run_action_factory(stdscr, action_entry)
                    except Exception as e:
                        self.set_status(str(e), 3)
                else:
                    action = self.menu_actions[current_row]
                    self.run_action(action)