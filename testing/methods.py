import socket
import sys

class tests:

    def __init__(self, stdscr):
        self.button_list = ["Connect Robot","Read LP configuration","Back", "Quit"]
        self.stdscr = stdscr

    def respond(self,selected):
        if selected == 'Connect Robot':
            self.connect_robot("127.0.0.1")
        if selected == 'Read LP configuration':
            self.read_LP_configuration('192.168.0.21')

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