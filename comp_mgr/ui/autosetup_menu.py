import copy
import curses
import logging
import os
import sys
import time
from comp_mgr.comp import Rorze
from comp_mgr.config import NETWORK, CONFIG_MENU_OPTIONS
from comp_mgr.exceptions import *
from comp_mgr.ui.common_ui import PopupMenu, draw_status_popup, ScrollingLog

logger = logging.getLogger(__name__)

class AutosetupMenu:
    def __init__(self, ip_list, component_dict):
        self.ip_list = ip_list
        self.button_list = []
        self.menu_items = ["- Start Autosetup","- Change system", "- Back", "- Quit"]
        self.system = None
        self.status_message = ""
        self.status_until = 0
        self.component_dict = component_dict

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
        # offset = self.ncomponents + len(self.menu_items) + 4
        # stdscr.addstr(offset, 4, f"Config: {self.system}")
        # for i, component in self.all_components.items():
        #     config_items = []
        #     display_name = f'{component['Type']}: '
        #     for item, cfg in component['Config_List'].items():
        #         enabled = cfg.get("enabled", False)
        #         string = f'{item} = {enabled} '
        #         if 'value' in cfg.keys():
        #             string += f' {cfg['value']}'
        #         config_items.append(string)
            
        #     display_config = " | ".join(config_items)
        #     display_full = display_name+display_config
        #     stdscr.addstr(offset + 1 + i, 4, display_full[:curses.COLS - 8])

        draw_status_popup(stdscr, self.status_message, self.status_until)
        stdscr.refresh()

    def run(self, stdscr):

        # Return if no system configuration was chosen
        ini = self.initialize_component_dict(stdscr, self.component_dict)
        if ini == 'cancel':
            return None

        curses.curs_set(0)
        stdscr.keypad(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        current_row = 0
        stdscr.timeout(500)

        while True:
            stdscr.clear()
            self.draw(stdscr, current_row)
            key = stdscr.getch()
            if key == curses.KEY_UP:
                current_row = (current_row - 1) % len(self.button_list)
                logger.debug(f"Current row: {current_row}")
            elif key == curses.KEY_DOWN:
                current_row = (current_row + 1) % len(self.button_list)
                logger.debug(f"Current row: {current_row}")
            elif key == ord('\n'):
                logger.debug(f"Current row: {current_row}")
                selected = self.button_list[current_row]
                if selected == '- Start Autosetup':
                    self.autosetup(stdscr)
                    break
                elif selected == '- Change system':
                    self.choose_system(stdscr)
                elif selected == '- Back':
                    break
                elif selected == '- Quit':
                    sys.exit(0)
                else:
                    self.configure_component(stdscr, current_row)
                    self.check_body_IP(current_row)
                    self.set_status(f"{self.all_components[current_row]['Type']} config updated")

    def choose_system(self, stdscr):
        options = {
            'WMC': {"label": "WMC", "type": "selection", "key": "system"},
            'SEMDEX': {"label": "SEMDEX", "type": "selection", "key": "system"}
        }
        popup = PopupMenu(stdscr, "Choose System", options)
        self.system = popup.run()

        stdscr.clear()
        stdscr.refresh()

        if self.system == None:
            return None

        for i, component in self.all_components.items():

            # Set component target system accordingly
            component['System'] = self.system

            # Set component target IP
            target_ip = NETWORK[self.system][component["Type"]]
            if component['IP'] == target_ip:
                self.all_components[i]['Config_List']['Configure']['enabled'] = False
                logger.info(f"Skipping Target IP for {component["SN"]}")
            else:
                self.all_components[i]['Config_List']['Configure']['enabled'] = True
                logger.info(f"Setting Target IP for {component["SN"]}")
            

    def configure_component(self, stdscr, current_row):
        """
        This method contains all different steps of configuration based on which component is fed to it.
        Data for each component is stored in config.py
        """
        for i, component in self.all_components.items():
            logger.debug(f"{i}, {component}")
        config_dict = self.all_components[current_row]['Config_List']
        popup = PopupMenu(stdscr, "Select Configuration", config_dict)
        popup.run()
        stdscr.clear()
        stdscr.refresh()

    def get_button(self, index) -> str:
        component = self.all_components[index]
        config_list = component['Config_List']

        ip = component["IP"]
        type = component["Type"]

        checkbox = f"[{'X' if config_list['Configure']['enabled'] == True else ' '}]"
        display = [f'{checkbox} {type} [']

        if config_list["Target_IP"]['enabled']:
            target_ip = config_list["Target_IP"]["value"]
        else:
            target_ip = NETWORK[self.system][component["Type"]]

        # If an update is enabled, include it to the information page
        if config_list['Configure']['enabled']:
            if ip != target_ip:
                display.append(f"{ip} -> {target_ip}")
            for config_item in config_list:
                if config_item == 'Configure': continue
                if config_list[config_item]['enabled']:
                    # Omit Change IP label, since that one is obvious by design
                    if not config_list[config_item]['label'] == "Change IP":
                        display_text = config_list[config_item]['label']
                        display.append(display_text)
        else: 
            display.append("Do not configure")
                
        # Concatenate display entries to a single button
        if len(display) > 1:
            button = display[0]+", ".join(display[1:])+"]"
        else:
            button = display[0]+"Nothing to do...]"
        
        return button

    def create_system_config(self, stdscr):
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

        if self.system == None:
            self.choose_system(stdscr)
            # If user selected back -> exit
            if self.system == None:
                return None

        # Set the target IP
        for component in self.all_components.values():
            target_ip = NETWORK[self.system][component['Type']]
            component['Config_List']['Target_IP']['value'] = target_ip
    
    def check_body_IP(self, component_ID):
        """When configuring a components' body no. -> Make sure the IP changes accordingly"""
        component = self.all_components[component_ID]
        if component['Config_List'].get('Set_Body_Number', False):
            body_no = component['Config_List']['Set_Body_Number']['value']
            if self.system == "WMC":
                self.all_components[component_ID]['Config_List']['Target_IP']['value'] = f'192.168.30.1{body_no}0'
            elif self.system == "SEMDEX":
                self.all_components[component_ID]['Config_List']['Target_IP']['value'] = f'192.168.0.2{body_no}'

    def check_loadport_configuration(self):
        """
        Method will check how many LPs are connected. Two cases have to be handled in case of multiple LPs:
        1. There are already configured loadports in the system -> Assign unconfigured LP a new Body number
        2. There are multiple unconfigured loadports connected -> Throw an exception due to possible IP conflicts
        (Later we could implement multi-LP setup)
        """
        configured = [False, False, False]
        unconfigured = []
        for idx, component in self.all_components.items():
            ctype = component["Type"]
            # Check, if there are any configured loadports within the system
            if ctype.startswith('Loadport_'):
                lp_no = int(component['Type'][-1])
                configured[lp_no-1] = True
                component['Config_List']['Set_Body_Number']['initial'] = lp_no
            elif ctype == 'Loadport (Unconfigured)':
                unconfigured.append(idx)

        if len(unconfigured) > 1:
            raise MultipleUnconfiguredLoadports(
                "Only connect one unconfigured loadport at once to avoid IP conflicts"
                )

        if unconfigured:
            logger.debug(f"Configured Loadports: {configured}")
            free_body = next(
                (i+1 for i, is_configured in enumerate(configured) if not is_configured),1
                )
            idx = unconfigured[0]
            unconf_component = self.all_components[idx]
            unconf_component['Config_List']['Set_Body_Number']['value'] = free_body
            unconf_component['Config_List']['Set_Body_Number']['enabled'] = True
            unconf_component['Type'] = f'Loadport_{free_body}'
        
    def check_prealigner_configuration(self):
        if self.system == "SEMDEX":
            PA_angle = 90000
        elif self.system == "WMC":
            PA_angle = 180000

        # Find Prealigner and change the setting
        for idx, component in self.all_components.items():
            ctype = component["Type"]
            if ctype == "Prealigner":
                logger.debug(self.all_components[idx])
                self.all_components[idx]['Config_List']['Notch_Angle']['value'] = PA_angle
    
    def initialize_component_dict(self, stdscr, component_dict):
        # For testing
        # all_components = {
        #     '172.20.9.150': {'IP': '172.20.9.150', 'System': None, 'Type': 'Prealigner', 'Name': 'ALN0', 'SN': 'ACE5CFG', 'Identifier': 'RA320_003', 'Firmware': '1.03B'},
            # '192.168.30.20': {'IP': '192.168.30.20', 'System': 'WMC', 'Type': 'Robot', 'Name': 'TRB0', 'SN': 'RC5J082', 'Identifier': 'RR754', 'Firmware': '1.19U'},
            # '192.168.30.110': {'IP': '192.168.30.110', 'System': 'WMC', 'Type': 'Loadport_1', 'Name': 'STG1', 'SN': 'STG1504', 'Identifier': 'RV201-F07-000', 'Firmware': '1.13R'},
            # '172.20.9.100': {'IP': '172.20.9.100', 'System': None, 'Type': 'Loadport (Unconfigured)', 'Name': 'STG0', 'SN': 'STG1503', 'Identifier': 'RV201-F07-000', 'Firmware': '1.13R'},
            # }

        all_components = component_dict

        self.all_components = {}

        component_idx = 0
        for i, ip in enumerate(all_components.keys()):
            # Check, whether a component is in the list of known components
            if all_components[ip]['Identifier'] in CONFIG_MENU_OPTIONS:
                self.all_components[component_idx] = all_components[ip]
                component_idx+=1
                # Set up a configuration list for each component
                type = self.all_components[i]['Identifier']
                config_list = CONFIG_MENU_OPTIONS['Common'] + CONFIG_MENU_OPTIONS[type]
                self.all_components[i]['Config_List'] = {}
                for config_item in config_list:
                    # Use deepcopy in order not to change the original dict in config.py
                    self.all_components[i]['Config_List'][config_item['key']] = copy.deepcopy(config_item)
            else: 
                logger.debug(f"Component {all_components[ip]['Identifier']} not implemented in autosetup")
        
        # Check, how to setup loadports
        self.check_loadport_configuration() 

        logger.info('=== AUTOSETUP COMPONENTS ===')
        for component in self.all_components.values():
            logger.info(f'{component['Type']} {component['Identifier']}')
            logger.debug(f'{component}')

        self.ncomponents = len(all_components)
        
        logger.info("Determining system config...")
        self.create_system_config(stdscr)
        if self.system == None:
            return "cancel"
        logger.info(f"System configuration: {self.system}")

        # Check, how to setup prealigner, after system is set
        self.check_prealigner_configuration()

        for i, component in self.all_components.items():
            target_ip = NETWORK[self.system][component["Type"]]
            if component['IP'] != target_ip:
                self.all_components[i]['Config_List']['Configure']['enabled'] = True
                self.all_components[i]['Config_List']['Target_IP']['enabled'] = True
            else:
                self.all_components[i]['Config_List']['Configure']['enabled'] = False
    
    def autosetup(self, stdscr):
        """
        Define here, which actions are taken when a Config_List entry is read.
        """
        # Start the log screen
        log = ScrollingLog(stdscr)
        log.add("Starting Autosetup...")

        for i, entry in self.all_components.items():
            
            # Check, if component should be configured
            if not entry['Config_List']['Configure']['enabled']: continue

            # Connect to component
            component = Rorze(entry)

            # temporary parsing - change to component.ip later
            ip = entry["IP"]
            identifier = entry["Identifier"]
            sn = entry["SN"]

            log.add(f"########## Processing {entry["Identifier"]} {entry["SN"]} ##########")
            # Save original component backup
            infostring = "Saving original component backup..."
            logger.info(infostring)
            log.add(infostring)
            component.read_data(suffix='_ORG')
            files = os.listdir()
            if not any(f'{sn}' in f for f in files):
                logger.error(f"Error during autosetup - No backup file was created for {sn}")
                logger.debug(f"Directory files: {files}")
                raise NoBackup("No backup file was created")

            # Start going through the possible config actions
            for config_item, config in entry['Config_List'].items():
                
                if config['enabled']:
                    if config_item == "Target_IP":
                        new_ip = config["value"]
                        if ip != new_ip:
                            infostring = f"Changing IP of {identifier} from {ip} to {new_ip}" 
                            logger.info(infostring)
                            log.add(infostring)
                            component.change_IP(new_ip,write=0)
                    if config_item == "Notch_Angle":
                        notch_angle = config["value"]
                        infostring = f"Setting notch angle of {identifier} to {notch_angle} mdeg"
                        logger.info(infostring)
                        log.add(infostring)
                        component.set_notch_angle(notch_angle,write=0)
                    elif config_item == "Basic_Settings":
                        infostring = "Applying basic settings..."
                        logger.info(infostring)
                        log.add(infostring)
                        component.basic_settings(write=0)
                    elif config_item == "Spindle_Fix":
                        infostring = "Removing Aligner Spindle offset..."
                        logger.info(infostring)
                        log.add(infostring)
                        component.spindle_fix(write=0)
                    elif config_item == "Slow_Mode":
                        infostring = "Setting aligner spindle speed to slow..."
                        logger.info(infostring)
                        log.add(infostring)
                        component.set_alignment_speed(speed="Slow",write=0)
                    elif config_item == "No_Interpolation":
                        infostring = "Disabling Interpolation..."
                        logger.info(infostring)
                        log.add(infostring)
                        component.no_interpolation(write=0)
                    elif config_item == "Flip_Near":
                        infostring = "Enabling flipping option of retracted arm..."
                        logger.info(infostring)
                        log.add(infostring)
                        component.set_flip_near("On",write=0)
                    elif config_item == "Set_Body_Number":
                        body_no = config["value"]
                        infostring = f"Setting body number of {identifier} to {body_no}..."
                        logger.info(infostring)
                        log.add(infostring)
                        component.set_body_no(body_no,write=0)
                    
            log.add("Writing changes to flash memory...")
            component.write_changes()

            log.add("Saving component backup...")
            # Save altered component backup
            component.read_data()

            logger.info(f"#################### Autosetup complete for {identifier} ####################")

        log.add("Autosetup done. Press any key to return...")
        stdscr.timeout(-1)
        stdscr.getch()
