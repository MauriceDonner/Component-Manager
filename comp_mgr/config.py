"""
Configuration module

Contains all configuration data, such as static IPs or configuration parameters that are not usually changed
"""

NETWORK = {
    "SEMDEX": {
        "Robot":         "192.168.0.1",
        "Pendant":       "192.168.0.2",
        "Lineartrack":   "192.168.0.3",
        "Loadport_1":    "192.168.0.21",
        "Loadport_2":    "192.168.0.22",
        "Loadport_3":    "192.168.0.23",
        "Prealigner":    "192.168.0.151",
        "WID_Reader":    "192.168.0.161",
    },
    "WMC": {
        "Cam_Handling":  "192.168.30.4",
        "Cam_Metrology": "192.168.30.5",
        "Pendant":       "192.168.30.6",
        "Robot":         "192.168.30.20",
        "Lineartrack":   "192.168.30.21",
        "WID_Reader":    "192.168.30.61",
        "Prealigner":    "192.168.30.70",
        "Loadport_1":    "192.168.30.110",
        "Loadport_2":    "192.168.30.120",
        "Loadport_3":    "192.168.30.130",
        "CID_Reader_1":  "192.168.30.111",
        "CID_Reader_2":  "192.168.30.112",
        "CID_Reader_3":  "192.168.30.113",
    },
    "UNCONF": {
        "Robot":         "172.20.9.150",
        "Lineartrack":   "172.20.9.140",
        "Loadport":      "172.20.9.100",
        "Prealigner":    "172.20.9.160",
    }
}

OTHER_IPS = {
    "127.0.0.1":     "Simulation",
    "172.20.9.100":  "Loadport (Unconfigured)",
    "172.20.9.101":  "Loadport (Unconfigured)",
    "172.20.9.140":  "Lineartrack (Unconfigured)",
    "172.20.9.150":  "Robot (Unconfigured)",
    "172.20.9.151":  "Robot (Unconfigured)",
    "172.20.9.160":  "Prealigner (Unconfigured)",
    "172.20.9.161":  "Prealigner (Unconfigured)",
    "172.20.9.220":  "Teaching Pendant (Unconfigured)",
    "192.168.0.10":  "SEMDEX Log Host",
    "192.168.30.1":  "WMC Software PC",
    "192.168.40.2":  "WMC Hardware PC",
    "192.168.30.55": "Reolink Camera",
    "192.168.30.56": "Reolink Camera",
    "192.168.30.57": "Reolink Camera",
    "192.168.30.58": "Reolink Camera",
    "192.168.30.59": "Reolink Camera",
    "192.168.60.55": "Reolink Camera",
    "192.168.60.56": "Reolink Camera",
    "192.168.60.57": "Reolink Camera",
    "192.168.60.58": "Reolink Camera",
    "192.168.60.59": "Reolink Camera",
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

class MESSAGES:
    SUCCESS = "Program ran successfully"