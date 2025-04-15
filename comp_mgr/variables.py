"""
Variables module

Contains all program variables, such as static IPs or configuration parameters that are not usually changed
"""

NETWORK = {
    #"SEMDEX": {
    #    "Robot":       "192.168.0.1",
    #    "Pendant":     "192.168.0.2",
    #    "Lineartrack": "192.168.0.3",
    #    "Log Host":    "192.168.0.10",
    #    "Loadport 1":  "192.168.0.21",
    #    "Loadport 2":  "192.168.0.22",
    #    "Loadport 3":  "192.168.0.23",
    #    "Prealigner":  "192.168.0.151",
    #},
    #"WMC": {
    #    "Robot":       "192.168.30.20",
    #    "Pendant":     "192.168.30.6",
    #    "Lineartrack": "192.168.30.21",
    #    "Log Host":    "192.168.30.1",
    #    "Loadport 1":  "192.168.30.111",
    #    "Loadport 2":  "192.168.30.121",
    #    "Loadport 3":  "192.168.30.131",
    #    "Prealigner":  "192.168.30.70",
    #},
    "UNCONF": {
        "Robot":       "172.20.9.150",
        "Pendant":     "172.20.9.???",
        "Lineartrack": "172.20.9.140",
        "Rorze LP":    "172.20.9.100",
        "Prealigner":  "172.20.9.160",
        "Simulation":  "127.0.0.1"
    }
}

#class Network:
#    def