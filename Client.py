import struct
import socket
import sys
import colorama
from threading import Timer
from scapy.arch import get_if_addr
import select

"""Approve only messages that contains this values"""
MAGIC_COOKIE_APPROVAL = 0xabcddcba
MESSAGE_TYPE_APPROVAL = 0x2
ETH = 'eth2'
PORT = 2515


class Client:
    """
    Client that's playing equation game
    """

    def __init__(self, port, team_name, udp_ip):
        """
        :param port: The port number of client app.
        :param team_name: client team name.
        """
        self.port = port
        self.team_name = team_name
        self.udp_ip = '.'.join(udp_ip.split('.')[:2]) + ".255.255"

        print(f"{colorama.Fore.GREEN}Client started, listening for offer requests...")
        while True:
            try:
                self.create_udp_socket()  # if UDP listen failed, start broadcast again.
            except:
                time.sleep(0.1)
                print(f"{colorama.Fore.RED}Failed to connect.")
                continue

    def create_udp_socket(self):
        """
        listen for request's
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.bind((self.udp_ip, self.port))

        while True:
            message, address = udp_socket.recvfrom(1024)

            print(f"{colorama.Fore.GREEN}Received offer from {address[0]},attempting to connect...")
            magic_cookie, message_type, server_port = None, None, None
            try:
                magic_cookie, message_type, server_port = struct.unpack(">IbH", message)
            except:
                magic_cookie, message_type, server_port = struct.unpack("IbH", message)

            if magic_cookie == MAGIC_COOKIE_APPROVAL and message_type == MESSAGE_TYPE_APPROVAL:  # verify reliable message
                self.connect(address, server_port)  # connect via TCP

    def connect(self, address, server_port):
        """
        :param address: sender address
        :param server_port: server listening port
        """
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.tcp_socket.connect((address[0], server_port))

        self.tcp_socket.send(bytes(self.team_name + "\n", "utf-8"))
        self.play()

    def play(self):
        """
        equation gameplay
        """
        print(self.tcp_socket.recv(1024).decode("utf-8"))
        self.tcp_socket.settimeout(11)

        answer, _, _ = select.select([sys.stdin, self.tcp_socket], [], [], 10)
        if answer and type(answer[0]) != type(self.tcp_socket):

            answer = sys.stdin.readline()[:-1]
            if len(answer) == 0:
                answer = 'a'
            self.tcp_socket.send(bytes(answer, "utf-8"))
            print(f"{self.team_name} answer is: {answer}")

        print(self.tcp_socket.recv(1024).decode("utf-8"))

        print(f"{colorama.Fore.GREEN}Server disconnected, listening for offer requests...")

        self.tcp_socket.close()


Client(PORT, "yuri2", get_if_addr(ETH))
