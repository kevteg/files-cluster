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
    def __init__(self, group_name):
        # Look up multicast group address in name server and find out IP version
        group = 'ff05:70aa:aaaa:3333:4444:2222:1111:6666'
        self.MYPORT = 8124
        self.addrinfo = socket.getaddrinfo(group, None)[0]
        # Create a socket
        self.sock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
        self.sock.bind(('', self.MYPORT))
        group_bin = socket.inet_pton(self.addrinfo[0], self.addrinfo[4][0])
        mreq = group_bin + struct.pack('@I', 0)
        self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)


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
parser.add_argument('-g','--group',dest='group_name',type=str, help='Group to connect in')

args = parser.parse_args()

clie = client(args.group_name)
clie.run()
