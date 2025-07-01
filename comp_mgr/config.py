"""
Configuration module

Contains all configuration data, such as static IPs or configuration parameters that are not usually changed
"""

NETWORK = {
    "SEMDEX": {
        "Robot":       "192.168.0.1",
        "Pendant":     "192.168.0.2",
        "Lineartrack": "192.168.0.3",
        "Log Host":    "192.168.0.10",
        "Loadport 1":  "192.168.0.21",
        "Loadport 2":  "192.168.0.22",
        "Loadport 3":  "192.168.0.23",
        "Prealigner":  "192.168.0.151",
    },
    "WMC": {
        "Robot":           "192.168.30.20",
        "Pendant":         "192.168.30.6",
        "Lineartrack":     "192.168.30.21",
        "Log Host":        "192.168.30.1",
        "Reolink_Han":     "192.168.30.4",
        "Reolink_Met":     "192.168.30.5",
        "Reolink_0":       "192.168.30.55",
        "Reolink_1":       "192.168.30.56",
        "Reolink_2":       "192.168.30.57",
        "Reolink_3":       "192.168.30.58",
        "Reolink_4":       "192.168.30.59",
        "Loadport 1":      "192.168.30.110",
        "Loadport 2":      "192.168.30.120",
        "Loadport 3":      "192.168.30.130",
        "Loadport 1 (!)":  "192.168.30.111",
        "Loadport 2 (!)":  "192.168.30.121",
        "Loadport 3 (!)":  "192.168.30.131",
        "Prealigner":      "192.168.30.70",
    },
    "UNCONF": {
        "Robot":          "172.20.9.150",
        "Robot (!)":      "172.20.9.151",
        #"Pendant":        "172.20.9.151",
        "Lineartrack":    "172.20.9.140",
        "Rorze LP":       "172.20.9.100",
        "Prealigner":     "172.20.9.160",
        "Prealigner (!)": "172.20.9.161",
        "Simulation":     "127.0.0.1"
    }
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