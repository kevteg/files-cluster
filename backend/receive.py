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
        # Look up multicast group address in name server and find out IP version
        group = 'ff05:70aa:aaaa:3333:4444:2222:1111:6666'
        self.addrinfo = socket.getaddrinfo(group, None)[0]
        self.MYPORT = 8124
        # Create a socket
        self.sock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
        self.sock.bind(('', self.MYPORT))
        group_bin = socket.inet_pton(self.addrinfo[0], self.addrinfo[4][0])
        mreq = group_bin + struct.pack('@I', 0)
        self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

        # Loop, printing any data we receive
        while True:
            data, sender = self.sock.recvfrom(1500)
            while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
            print (str(sender) + '  ' + repr(data))

    def run(self):
        print("Starting server")
        self.dowork = True
        reader = threading.Thread(name='read', target=self.read)
        reader.start()

    def read(self):
        print("Starting to read from server")
        while self.dowork:
            data, sender = self.sock.recvfrom(1500)
            while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
            print (str(sender) + '  ' + repr(data))
        print("Stoping")
        self.sock.close()


parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to receive changes in directory to a multicast group.')
parser.add_argument('-s','--send',dest='send_multicast',type=str, default="230.1.1.1", help='Multicast address to send data')
parser.add_argument('-i','--send_port',dest='send_port',type=int, default=5000, help='Multicast port to send data')

args = parser.parse_args()

clie = client(args.send_multicast, args.send_port)
clie.run()