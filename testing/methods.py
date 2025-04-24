import socket
import sys

class tests:

    def __init__(self, stdscr):
        self.button_list = ["Connect Robot","Test","Back", "Quit"]
        self.stdscr = stdscr

    def respond(self,selected):
        if selected == 'Test':
            self.test_test()
        if selected == 'Connect Robot':
            self.connect_robot("127.0.0.1")

    def test_test(self):
        self.stdscr.addstr(8,0,'hi')
    
    def connect_robot(self,ip,port=12100):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        row = len(self.button_list)+3
        try:
            sock.connect((ip,port))

            # Show response
            self.stdscr.addstr(row,0,sock.recv(1024))
            self.stdscr.addstr(row+1,0,'Press a key to start origin search')
            self.stdscr.getch()

            # Send origin search command
            command = "oTRB1.ORGN(0,0)"
            sock.sendall(command.encode('utf-8'))
            self.stdscr.addstr(row+2,0,sock.recv(1024))
            sock.close()
        except socket.timeout:
            self.stdscr.addstr(row,0,'Timeout')
        except socket.error as e:
            self.stdscr.addstr(row,0,f'Socket error: {e}')
        finally:
            sock.close()