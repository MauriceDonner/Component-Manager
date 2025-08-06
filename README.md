# Component Manager (README WIP)

This software scans the local network for all known component IPs (defined in [variables.py](comp_mgr/variables.py)), and offers a method to automatically configure them for either SemDex or WMC systems.

## Running the software

A compiled version of the software can be found in `releases`. Simply run `ComponentManager.exe` on a Windows system.

## The way it works

### 1. Network discovery 

The program tries to ping all known component IPs, and creates an instance of the `Component` class for each response, containing information about IP, current configuration and component type.

### 2. Menu

The main menu lists all components in the local network. From here, either all components can be configured according to a WMC or SemDex network standard.

Alternatively, single components can be selected and configured individually.

### 3. Component list and configuration settings

The type of components and their configurations can be found in the list below:

- Loadport
    - [ ] Find serial Number
    - [ ] Find Loadport type
    - [ ] Read firmware version 
    - [ ] Backup original settings
    - [x] Read rotary switch value
    - [ ] Set settings for specific Body No.
        - Body No
        - Auto Output
        - TCP/IP
        - Host IP Adr.
        - Log Host
        - Own IP
        - Presence led
        - i/o
    - [ ] Backup new settings
    - [ ] All axis origin search
    - [ ] (Ask user for Load/Endurance test)
- Prealigner
    - [ ] Find serial number
    - [ ] Find Prealigner type
    - [ ] Read firmware version
    - [ ] Backup original settings
    - [ ] Set settings
        - Host IP Address
        - Host Port
        - Log Host
        - Host Interface
        - Body No
    - [ ] Backup new settings
    - [ ] All axis origin search
    - [ ] Ask user for Endurance test
- Lineartrack  
    - [ ] Find serial number
    - [ ] Backup original settings
    - [ ] Set settings
        - Host IP Address
        - Host Port
        - Log Host
    - [ ] Backup new settings
- Robot
    - [ ] Find serial number
    - [ ] Find robot type
    - [ ] Read firmware version
    - [ ] Backup original settings
    - [ ] Set settings
        - Host IP Address
        - Host Port
        - Log Host
        - Own IP Address
        - No Interpolation
    - [ ] Backup new settings
    - [ ] All axis origin search
- Teaching Pendant
    - Only check for connection, settings are changed within Pendant
- Log Host
    - Only check for connection. No settings are changed.

## Compiling and testing the software

The software is built using PyInstaller:

```
pyinstaller --onefile --icon=CM_Icon.ico --name ComponentManager comp_mgr/__main__.py
```

To quickly test the software without having to compile, make sure you have Python 3.13 installed on your system. Then run

```
python -m comp_mgr
```

from the `Component Manager` directory.
