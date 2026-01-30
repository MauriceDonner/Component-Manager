# Component Manager (README WIP)

This software scans the local network for all known component IPs (defined in [variables.py](comp_mgr/variables.py)), and offers a method to automatically configure them for either SemDex or WMC systems.

## Running the software

A compiled version of the software can be found in `releases`. Simply run `ComponentManager.exe` on a Windows system.

## The way it works

### 1. Network discovery 

The program tries to ping all known component IPs, and creates an instance of the `Component` class for each response, containing information about IP, current configuration and component type.

### 2. Main Menu

The main menu lists all components in the local network. From here, either all components can be configured according to a WMC or SemDex network standard.

Alternatively, single components can be selected and configured individually.

### 3. Component Menu

Press the Enter Key with a component selected to connect to that component. Once connected, you can read all kinds of status information, or change settings for that component. Each component has different settings. Settings can be added by request.

### 4. Autosetup Menu

All connected components are listed. The Menu shows a summary of which settings are going to be changed. Pressing the Enter Key on a component lets you change its configuration. Nothing is communicated to the component until the "Start Autosetup" option is chosen. This option will then communicate the configuration to all components. **It also creates backups before and after changes are made**, which makes this software safe to operate, even if a bug is not discovered in time.

## 3. List of Settings

The type of components and their configurations can be found in the list below:

- Loadport
    - [x] Find serial Number
    - [x] Read firmware version 
    - [x] Backup original settings
    - [x] Change IP address
    - [x] Set body no.
    - [ ] Set basic settings (which are always the same within a system):
        - Auto output
        - TCP/IP
        - Host IP adr.
        - Log host
        - Presence led
        - i/o
    - [x] Backup new settings
    - [ ] All axis origin search
    - [ ] (Ask user for load/endurance test?)
- Prealigner
    - [x] Find serial number
    - [x] Find prealigner type
    - [x] Read firmware version
    - [x] Backup original settings
    - [x] Change IP address
    - [x] Set spindle tolerance to 0 (only RA320_003)
    - [x] Set slow prealigner spindle speed (for the external notch camera)
    - [ ] Set basic settings (which are always the same within a system):
        - Host IP address
        - Host port
        - Log host
        - Host interface
        - Body no
    - [x] Backup new settings
    - [ ] All axis origin search
    - [ ] Ask user for endurance test?
- Lineartrack  
    - [x] Find serial number
    - [x] Backup original settings
    - [x] Change IP address
    - [ ] Set basic settings (which are always the same within a system):
        - Host IP Address
        - Host Port
        - Log Host
    - [x] Backup new settings
- Robot
    - [x] Find serial number
    - [x] Find robot type
    - [x] Read firmware version
    - [x] Backup original settings
    - [x] Change IP address
    - [ ] Set basic settings (which are always the same within a system)
        - Host IP Address
        - Host Port
        - Log Host
        - No Interpolation
    - [x] Backup new settings
    - [ ] All axis origin search

## List of integrated components

- Rorze Robot **RR754**
- Rorze Linear Track **RTS13**
- Rorze Prealigners
    - **RA320**
    - **RA320_003**
    - **RA420_001**
- Rorze Loadport
    - **RV201-F07-000**

For safety reasons, any other component will not be able to be configured unless it is manually added.

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