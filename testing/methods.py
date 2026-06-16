import logging
import concurrent.futures
import os
import socket
import subprocess
from datetime import datetime
from comp_mgr.comp_if import CompIF
from comp_mgr.config import NETWORK
from comp_mgr.ui.common_ui import PopupInput
from typing import TextIO

logger = logging.getLogger(__name__)

class tests:

    def __init__(self, stdscr):
        self.button_list = ["Scan subnets","Back", "Quit"]
        self.stdscr = stdscr

    def write_file(self):
        # Timestamp
        self.sn = "TEST123"
        ts = datetime.now().strftime("%Y%m%d")
        index = 1
        filename = f"{self.sn}_{ts}_{index}.dat"
        logger.debug(f"Reading data to {filename}")

        # Make sure to not overwrite a previous backup
        file_exists = 1 if os.path.exists(filename) else 0
        while file_exists:
            index+=1
            filename = f"{self.sn}_{ts}_{index}.dat"
            logger.warning(f"File exists! Changing filename to {filename}")
            if not os.path.exists(filename):
                break
        
        string=f"Writing to file {filename}..."
        logger.info(string)
        with open(f"{filename}", "w") as testfile:
            self.read_block(string, filename, testfile)
        
        return string
        
    def read_block(self, string: str, filename: str, file: TextIO):
        print(f"Writing to file {filename}...", file=file)

    def respond(self,selected) -> str:
        if selected == 'Connect Robot':
            response = self.connect_robot("127.0.0.1")
        if selected == 'Read LP configuration':
            response = self.read_LP_configuration('192.168.0.21')
        if selected == 'Get component info':
            response = self.get_info()
        if selected == 'Write File':
            response = self.write_file()
        if selected == 'Scan subnets':
            response = self.scan_subnet()
        
        return response

    def connect_robot(self,ip,port=12100):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        row = len(self.button_list)+3
        try:
            sock.connect((ip,port))

            # Show response
            self.stdscr.addstr(row,0,sock.recv(1024))

            # Prompt user to start origin search
            command = "oTRB1.ORGN(0,0)"
            self.stdscr.addstr(row+1,0,'Press a key to start origin search')
            self.stdscr.getch()
            sock.sendall(command.encode())

            # Show response and close
            self.stdscr.addstr(row+2,0,sock.recv(1024))
            sock.close()

        # Make sure to not crash the program when TCP/IP connection failed
        except socket.timeout:
            self.stdscr.addstr(row,0,'Connection Timeout. Is the component connected?')
        except socket.error as e:
            self.stdscr.addstr(row,0,f'Socket error: {e}')
        finally:
            sock.close()
    
    # def send_and_rcv_command(self,command: list,ip,port=12100)
    def read_LP_configuration(self,ip,port=12100):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        row = len(self.button_list)+3
        try:
            sock.connect((ip,port))

            # Show response
            self.stdscr.addstr(row,0,sock.recv(1024))

            # Read Firmware
            sock.sendall("oSTG1.GVER".encode('utf-8'))
            firmware = sock.recv(1024)

            # Read Rotary switch position
            sock.sendall("oSTG1.GTDT3".encode('utf-8'))
            switch_pos = sock.recv(1024)

            # Read Loadport IP
            sock.sendall("oSTG1.GTDT1".encode('utf-8'))
            IP = sock.recv(1024)

            self.stdscr.addstr(row+2,0,f"Firmware: {firmware}")
            self.stdscr.addstr(row+3,0,f"Rotary switch position: {switch_pos}")
            self.stdscr.addstr(row+3,0,f"IP: {IP}")
            sock.close()

        # Make sure to not crash the program when TCP/IP connection failed
        except socket.timeout:
            self.stdscr.addstr(row,0,'Connection Timeout. Is the component connected?')
        except socket.error as e:
            self.stdscr.addstr(row,0,f'Socket error: {e}')
        finally:
            sock.close()
    
    def get_info(self, ip="192.168.0.21"):
        comp_if = CompIF()
        ip_info = comp_if.get_component_info(ip)
        logger.info(f"ip info: {ip_info}")
        return ip_info

    def ping(self, ip):
        command = ["ping", "-n", "1", "-w", "1000", ip] # 1000ms timeout
        result = subprocess.run(command, stdout=subprocess.DEVNULL)
        return ip if result.returncode == 0 else None

    def scan_subnet(self):
        subnet_1 = "192.168.0"
        subnet_2 = "192.168.30"
        subnet_3 = "192.168.10"

        ips_1 = [f"{subnet_1}.{octet}" for octet in range(255)]
        ips_2 = [f"{subnet_2}.{octet}" for octet in range(255)]
        ips_3 = [f"{subnet_3}.{octet}" for octet in range(255)]

        ips = ips_1 + ips_2 + ips_3
        alive = []
        n_workers = len(ips)

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
            results = executor.map(self.ping, ips)
            for result in results:
                if result:
                    alive.append(result)
        
        logger.debug("Scanning subnets...")
        logger.debug(str(alive))
        return str(alive)