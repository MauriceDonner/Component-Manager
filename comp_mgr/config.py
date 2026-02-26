"""
Configuration module

Contains all configuration data, such as static IPs or configuration parameters that are not usually changed
"""

NETWORK = {
    "SEMDEX": {
        "Robot":         "192.168.0.1",
        "Lineartrack":   "192.168.0.3",
        "Loadport_1":    "192.168.0.21",
        "Loadport_2":    "192.168.0.22",
        "Loadport_3":    "192.168.0.23",
        "Prealigner":    "192.168.0.151",
    },
    "WMC": {
        "Cam_Handling":  "192.168.30.4",
        "Cam_Metrology": "192.168.30.5",
        "Pendant":       "192.168.30.6",
        "Robot":         "192.168.30.20",
        "Lineartrack":   "192.168.30.21",
        "WID_Reader":    "192.168.30.61",
        "WID_Reader 2":  "192.168.30.62",
        "WID_Reader 3":  "192.168.30.63",
        "Prealigner":    "192.168.30.70",
        "Loadport_1":    "192.168.30.110",
        "Loadport_2":    "192.168.30.120",
        "Loadport_3":    "192.168.30.130",
        "CID_Reader_1":  "192.168.30.111",
        "CID_Reader_2":  "192.168.30.112",
        "CID_Reader_3":  "192.168.30.113",
    },
}

LOADPORTS = ["RV201-F07-000"]
ROBOTS = ["RR754"]
PREALIGNERS = ["RA320_002", "RA320_003", "RA420_001"]
OTHER = ["SIM_COMPONENT", "RTS13"]

OTHER_IPS = {
    # "127.0.0.1":     "Simulation",
    "172.20.9.100":  "Loadport (Unconfigured)",
    "172.20.9.101":  "Loadport (Unconfigured)",
    "172.20.9.140":  "Lineartrack (Unconfigured)",
    "172.20.9.150":  "Robot (Unconfigured)",
    "172.20.9.151":  "Robot (Unconfigured)",
    "172.20.9.160":  "Prealigner (Unconfigured)",
    "172.20.9.161":  "Prealigner (Unconfigured)",
    "172.20.9.220":  "Teaching Pendant (Unconfigured)",
    "192.168.0.2":   "SEMDEX Teaching Pendant",
    "192.168.0.161": "SEMDEX WID reader",
    "192.168.30.1":  "WMC Software PC",
    "192.168.40.2":  "WMC Hardware PC",
    "192.168.30.55": "Reolink Camera (?)",
    "192.168.30.56": "Reolink Camera (?)",
    "192.168.30.57": "Reolink Camera (?)",
    "192.168.30.58": "Reolink Camera (?)",
    "192.168.30.59": "Reolink Camera (?)",
    "192.168.30.240":"Reolink Camera (?)",
    "192.168.30.241":"Reolink Camera (?)",
    "192.168.60.55": "Reolink Camera (?)",
    "192.168.60.56": "Reolink Camera (?)",
    "192.168.60.57": "Reolink Camera (?)",
    "192.168.60.58": "Reolink Camera (?)",
    "192.168.60.59": "Reolink Camera (?)",
}

CANCEL_CODES = {
    "0001": "Command not designated",
    "0002": "The designated target motion not equipped",
    "0003": "Too many/too few parameters (number of elements)",
    "0004": "Command not equipped",
    "0005": "Too many/too few parameters",
    "0006": "Abnormal range of the parameter",
    "0007": "Abnormal mode",
    "0008": "Abnormal data",
    "0009": "System in preparation",
    "000A": "Origin search not completed",
    "000B": "Moving/Processing",
    "000C": "No motion",
    "000D": "Abnormal flash memory",
    "000E": "Insufficient memory",
    "000F": "Error-occurred state",
    "0010": "Origin search is completed but the motion cannot be started due to interlock",
    "0011": "The emergency stop signal is turned on.",
    "0012": "The temporarily stop signal is turned on.",
    "0013": "Abnormal interlock signal",
    "0014": "Drive power is turned off.",
    "0015": "Not excited",
    "0016": "Abnormal current position",
    "0017": "Abnormal target position",
    "0018": "Command processing",
    "0019": "Invalid work state"
}

# Add individual component settings here
CONFIG_MENU_OPTIONS = {
    'Common': [
        {'label': 'Configure Component', 'type': 'checkbox', 'key': 'Configure', 'enabled': False},
        {'label': 'Change IP', 'type': 'value', 'key': 'Target_IP', 'value': None, 'enabled': False},
        {'label': 'Basic settings', 'type': 'checkbox', 'key': 'Basic_Settings', 'enabled': True}
    ],
    'RA320_003': [
        { 'label': 'Spindle tolerance fix', 'type': 'checkbox', 'key': 'Spindle_Fix', 'enabled': True},
        { 'label': 'Slow mode (Ext. notch)', 'type': 'checkbox', 'key': 'Slow_Mode', 'enabled': False},
    ],
    'RR754': [
        { 'label': 'No interpolation', 'type': 'checkbox', 'key': 'No_Interpolation', 'enabled': True},
        { 'label': 'Init flip axis', 'type': 'checkbox', 'key': 'Init_Rotate', 'enabled': True},
    ],
    'RA420_001': [],
    'RTS13': [],
    'RV201-F07-000': [
        { 'label': 'Set Body Number', 'type': 'sub_selection', 'options': [1,2,3], 'key': 'Set_Body_Number', 'value': None, 'initial': None, 'enabled': False }
    ]
}

COMPONENT_MENU_OPTIONS = {
    'Common': [
        {'label': 'Get Status', 'type': 'command', 'action': 'get_status'},
        {'label': 'Change IP', 'type': 'value', 'action': 'change_IP', 'action_factory': 'change_IP_popup'},
        {'label': 'Set Log Host IP', 'type': 'value', 'action': 'set_log_host', 'action_factory': 'change_log_host_popup'},
        {'label': 'Create backup (Read Data)', 'type': 'command', 'action': 'read_data'}
    ],
    # 'SIM_COMPONENT': [
    #     {'label': 'Get Rotary Switch Position', 'type': 'command', 'action': 'get_rotary_switch_value'},
    #     {'label': 'Set upper arm laser', 'type': 'selection', 'action': 'set_laser', 'action_factory': 'upper_laser_popup'},
    #     {'label': 'Set lower arm laser', 'type': 'selection', 'action': 'set_laser', 'action_factory': 'lower_laser_popup'},
    # ],
    'RR754': [
        {'label': 'Read External Sensors (GAIO)', 'type': 'command', 'action': 'GAIO'},
        {'label': 'Set Automatic Status Reports ON (SAIO)', 'type': 'command', 'action': 'SAIO_on'},
        {'label': 'Set Automatic Status Reports OFF (SAIO)', 'type': 'command', 'action': 'SAIO_off'},
        {'label': 'Set upper arm laser', 'type': 'selection', 'action': 'set_laser', 'action_factory': 'upper_laser_popup'},
        {'label': 'Set lower arm laser', 'type': 'selection', 'action': 'set_laser', 'action_factory': 'lower_laser_popup'},
        {'label': 'No Interpolation', 'type': 'command', 'action': 'no_interpolation'}
    ],
    'RV201-F07-000': [
        {'label': 'Get Rotary Switch Position', 'type': 'command', 'action': 'get_rotary_switch_value'}
    ]
}

        #TODO Implement Toggle menu ? (overkill for now)
        # {'label': 'Toggle Sensors ON/OFF', 'type': 'toggle_menu', 'options': ['Upper Arm Laser', 'Lower Arm Laser'], 'key': None}

class MESSAGES:
    SUCCESS = "Program ran successfully"