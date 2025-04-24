# Component Manager (README WIP)

This software scans the local network for all known component IPs (defined in [variables.py](comp_mgr/variables.py)), and offers a method to automatically configure them for either SemDex or WMC systems.

## Running the software

A compiled version of the software can be found in [dist](dist/). Simply run `ComponentManager.exe` on a Windows system.

## The way it works

### 1. Network discovery 

The program tries to ping all known component IPs, and creates an instance of the `Component` class for each response, containing information about IP, current configuration and component type.

### 2. Menu

The main menu lists all components in the local network. From here, either all components can be configured according to a WMC or SemDex network standard.

Alternatively, single components can be selected and configured individually.

### 3. Component list and configuration settings

The type of components and their configurations can be found in the list below:

- Loadport
    - `WMC:    ` Standard IP: `192.168.30.111` (*.121 for second)
    - `SemDex: ` Standard IP: `192.168.0.21` (*.22 for second)
- Robot
- Teaching Pendant
- Lineartrack
- Log Host
- Prealigner

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
