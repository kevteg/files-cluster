#!/usr/bin/env python
# -*- coding: utf-8 -*
import time
import socket
import threading
import struct
import os
import argparse
'''
    Author: Keeeevin
'''
class client():
    def __init__(self, receive_multicast_group, receive_udp_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', receive_udp_port))
        mreq = struct.pack("4sl", socket.inet_aton(receive_multicast_group), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def run(self):
        print("Starting server")
        self.dowork = True
        reader = threading.Thread(name='read', target=self.read)
        reader.start()

    def read(self):
        print("Starting to read from server")
        while self.dowork:
            print("Receiving: " + self.sock.recv(10240).decode('utf-8'))
        print("Stoping")
        self.sock.close()


parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to receive changes in directory to a multicast group.')
parser.add_argument('-s','--send',dest='send_multicast',type=str, default="230.1.1.1", help='Multicast address to send data')
parser.add_argument('-i','--send_port',dest='send_port',type=int, default=5000, help='Multicast port to send data')

args = parser.parse_args()

clie = client(args.send_multicast, args.send_port)
clie.run()
