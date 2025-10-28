import curses
import logging
import sys
import time
from comp_mgr.comp_if import CompIF
from comp_mgr.config import NETWORK, CONFIG_MENU_OPTIONS
from comp_mgr.exceptions import MultipleUnconfiguredLoadports, DoubleConfiguration
from comp_mgr.ui.common_ui import PopupMenu, draw_status_popup

logger = logging.getLogger(__name__)

class AutosetupMenu:
    def __init__(self, ip_list, all_components):
        self.ip_list = ip_list
        self.button_list = []
        self.menu_items = ["- Start Autosetup","- Change system", "- Back", "- Quit"]
        self.system = None
        self.status_message = ""
        self.status_until = 0

        # TODO For testing
        all_components = {
            '172.20.9.150': {'IP': '172.20.9.150', 'System': None, 'Type': 'Prealigner', 'Name': 'ALN0', 'SN': 'ACE5CFG', 'CType': 'RA320_003', 'Firmware': '1.03B'},
            '192.168.30.20': {'IP': '192.168.30.20', 'System': 'WMC', 'Type': 'Robot', 'Name': 'TRB0', 'SN': 'RC5J082', 'CType': 'RR754', 'Firmware': '1.19U'},
            #'192.168.30.110': {'IP': '192.168.30.110', 'System': 'WMC', 'Type': 'Loadport_1', 'Name': 'STG1', 'SN': 'STG1504', 'CType': 'RV201-F07-000', 'Firmware': '1.13R'},
            '172.20.9.100': {'IP': '172.20.9.100', 'System': None, 'Type': 'Loadport (Unconfigured)', 'Name': 'STG0', 'SN': 'STG1503', 'CType': 'RV201-F07-000', 'Firmware': '1.13R'},
            }

        self.all_components = {}
        for i, ip in enumerate(all_components.keys()):
            # Check, whether a component is in the list of known components
            if all_components[ip]['CType'] in CONFIG_MENU_OPTIONS:
                # Assign an index for each recognized component
                self.all_components[i] = all_components[ip]
                self.all_components[i]['Configure'] = True
                # Set up a configuration list for each component
                type = self.all_components[i]['CType']
                config_list = CONFIG_MENU_OPTIONS['Common'] + CONFIG_MENU_OPTIONS[type]
                self.all_components[i]['Config_List'] = {}
                for config_item in config_list:
                    self.all_components[i]['Config_List'][config_item['key']] = config_item
            else: 
                logger.warning(f"Component {all_components[ip]['CType']} not implemented in autosetup")
        
        # Check, how to setup loadports
        self.check_loadport_configuration() 

        logger.debug('=== AUTOSETUP COMPONENTS ===')
        for component in self.all_components.values():
            logger.debug(f'{component}')

        self.ncomponents = len(all_components)
        
        self.create_system_config()
    
    def set_status(self, msg, duration=3):
        self.status_message = msg
        self.status_until = time.time() + duration

    def draw(self, stdscr, current_row):
        button_list = []

        # Create a button list from component list
        for i, component in self.all_components.items():
            button = self.get_button(i)
            button_list.append(button)
        button_list += self.menu_items

        self.button_list = button_list

        for i, row in enumerate(self.button_list):
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 4, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 2, 4, row)
            
        # For debugging, show the entire dict and system config
        offset = self.ncomponents + len(self.menu_items) + 4
        stdscr.addstr(offset, 4, f"Config: {self.config}")
        for i, component in self.all_components.items():
            config_items = []
            display_name = f'{component['Type']}: '
            for item, cfg in component['Config_List'].items():
                enabled = cfg.get("enabled", False)
                string = f'{item} = {enabled} '
                config_items.append(string)
            
            display_config = " | ".join(config_items)
            display_full = display_name+display_config
            stdscr.addstr(offset + 1 + i, 4, display_full[:curses.COLS - 8])

        draw_status_popup(stdscr, self.status_message, self.status_until)
        stdscr.refresh()

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        current_row = 0
        stdscr.timeout(500)

        if self.system == None:
            self.choose_system(stdscr)

        while True:
            stdscr.clear()
            self.draw(stdscr, current_row)
            key = stdscr.getch()
            if key == curses.KEY_UP:
                current_row = (current_row - 1) % len(self.button_list)
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(self.button_list)
            elif key == ord('\n'):
                selected = self.button_list[current_row]
                if selected.startswith('['):
                    component = self.all_components[current_row]['CType']
                    self.set_status(component)
                    # self.configuration_menu(stdscr)
                elif selected == '- Change system':
                    self.choose_system(stdscr)
                elif selected == '- Back':
                    break
                elif selected == '- Quit':
                    sys.exit(0)

    def choose_system(self, stdscr):
        options = [
            {"label": "WMC", "type": "selection", "key": "system"},
            {"label": "SEMDEX", "type": "selection", "key": "system"}
        ]
        popup = PopupMenu(stdscr, "Choose System", options, self.config)
        popup.run()

        stdscr.clear()
        stdscr.refresh()

    def configure_component(self, component):
        """
        This method contains all different steps of configuration based on which component is fed to it.
        Data for each component is stored in config.py
        """
        options = CONFIG_MENU_OPTIONS[component['Type']]
        for i, component in self.all_components.items():
            if not component['System']:
                component['Configure'] = True
            else:
                component['Configure'] = False

    def get_button(self, index) -> str:
        component = self.all_components[index]
        # If an unconfigured Loadport is connected, choose its Target Body
        if component["Name"].startswith("Loadport"):
            self.all_components[index]['Config_List']["Target_IP"]['enabled'] = True

        ip = component["IP"]
        type = component["Type"]

        # Choose a target IP, if no target ip is selected, just take the default IP
        if component["Config_List"]["Target_IP"]['enabled']:
            target_ip = component["Config_List"]["Target_IP"]["IP"]
        else:
            target_ip = NETWORK[self.config["system"]][type]
        
        self.all_components[index]['Configure'] = False if ip == target_ip else True

        checkbox = f"[{'X' if component["Configure"] == True else ' '}]"
        display = [f'{checkbox} {type} [']

        # If an update is enabled, include it to the information page
        if component["Configure"]:
            if ip != target_ip:
                display.append(f"{ip} -> {target_ip}")
            for config_item in component["Config_List"]:
                if component["Config_List"][config_item]['enabled']:
                    display_text = component["Config_List"][config_item]['label']
                    display.append(display_text) #TODO write Config_list into all_components
        else: 
            display.append(f"Do not configure")
                
        # Concatenate display entries to a single button
        if len(display) > 1:
            button = display[0]+", ".join(display[1:])+"]"
        else:
            button = display[0]+"Nothing to do...]"
        
        return button

    def load_testing_dict(self) -> dict:
        dict = {
            0: {
                'IP': '172.20.9.150', 'System': None, 'Type': 'Prealigner', 'Name': 'ALN1', 'SN': 'ACE5CFG',
                'CType': 'RA420_001', 'Firmware': '1.05A', 'Configure': True,
                'Config_List': {
                    'Basic_Settings': {'enabled': True},
                    'Target_IP': {'enabled': False, 'label': 'Change target IP', 'IP': None},
                    'Spindle_Fix': {'enabled': True, 'label': 'Spindle offset fix'},
                    'Speed_Fix': {'enabled': True, 'label': 'Low Speed fix'},
                }
            },
            1: {
                'IP': '172.20.9.100', 'System': None, 'Type': 'Loadport_1', 'Name': 'STG1', 'SN': 'STG1503',
                'CType': 'RV201-F07-000', 'Firmware': '1.13R', 'Configure': True,
                'Config_List': {
                    'Basic_Settings': {'enabled': True},
                    'Target_IP': {'enabled': False, 'label': 'Change target IP', 'IP': None},
                }
            },
            2: {
                'IP': '192.168.30.20', 'System': 'WMC', 'Type': 'Robot', 'Name': 'TRB1', 'SN': 'TRB1385',
                'CType': 'RR754', 'Firmware': '1.20Q', 'Configure': False, 
                'Config_List': {
                    'Basic_Settings': {'enabled': True},
                    'Target_IP': {'enabled': False, 'label': 'Change target IP', 'IP': None},
                    'No_Interpolation': {'enabled': True, 'label': 'Disable Interpolation'},
                    'Init_Rotate': {'enabled': True, 'label': 'Initialize Rotation axis'},
                }
            }
        }

        return dict

    def create_system_config(self):
        # Check whether to setup for SemDex or WMC ip space
        if any(component['IP'].startswith('192.168.0.') for i, component in self.all_components.items()):
            self.system = "SEMDEX"
            logger.info("SEMDEX IP found. Choosing System: SEMDEX")
        elif any(component['IP'].startswith('192.168.30.') for i, component in self.all_components.items()):
            if self.system == "SEMDEX":
                logger.error("Both WMC and SemDex configurations found!")
                raise DoubleConfiguration("Both WMC and SemDex configurations found!")
            logger.info("WMC IP found. Choosing System: WMC")
            self.system = "WMC"
        # Save this information to the global config
        self.config = {"system": self.system}
    
    def check_loadport_configuration(self):
        configured_loadports = [False, False, False]
        unconfigured_loadport_present = False
        unconf_index = []
        body_number = 1
        for i, component in self.all_components.items():
            # Check, if there are any configured loadports within the system
            if component["Type"].startswith('Loadport_'):
                lp_no = int(component['Type'][-1])
                configured_loadports[lp_no-1] = True
            # Also check, whether there is an unconfigured loadport
            if component["Type"] == 'Loadport (Unconfigured)':
                unconfigured_loadport_present = True
                unconf_index.append(i)

        if len(unconf_index) > 1:
            raise MultipleUnconfiguredLoadports("Only connect one unconfigured loadport at once to avoid IP conflicts")

        if unconfigured_loadport_present:
            logger.debug(f"unconfigured loadport present {configured_loadports}")
            if any(loadport == True for loadport in configured_loadports):
                # Set the smallest available body number
                for i in range(3):
                    if not configured_loadports[i]:
                        body_number = i+1
                        break
            self.all_components[unconf_index[0]]['Config_List']['Set_Body_Number']['value'] = body_number
            self.all_components[unconf_index[0]]['Type'] = f'Loadport_{body_number}'

        else:
            return 0
        