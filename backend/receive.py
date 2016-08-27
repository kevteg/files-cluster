#!/usr/bin/env python
# -*- coding: utf-8 -*
import time
import socket
import threading
import struct
import os
import argparse
import binascii
'''
    Author: Keeeevin
'''
class client():
    def __init__(self, group_name):

        # Look up multicast group address in name server and find out IP version

        group, self.MYPORT = self.getConnectionInfo(group_name)
        print("Created IP: " + group + ", port: " + str(self.MYPORT))
        self.addrinfo = socket.getaddrinfo(group, None)[0]
        # Create a socket
        self.sock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
        self.sock.bind(('', self.MYPORT))
        group_bin = socket.inet_pton(self.addrinfo[0], self.addrinfo[4][0])
        mreq = group_bin + struct.pack('@I', 0)
        self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    def getConnectionInfo(self, group_name):
        text = (binascii.hexlify(group_name.encode('utf-8')).decode())
        port = int('0x' + text[1:4], 0)
        port = port + 5000
        cafe = 'cafe'
        ip = "ff05"
        index = 0
        lon = len(text)
        if lon > 29:
            text = text[0:28]

        for i in range(1, 29 - lon):
            text += cafe[index]
            index = 0 if not i%4 else index + 1

        for index, i in enumerate(text, start = 0):
            ip += i if index%4 else ':' + i

        return ip, port


    def run(self):
        print("Starting receiver")
        self.dowork = True
        reader = threading.Thread(name='read', target=self.read)
        writer = threading.Thread(name='write', target=self.write)
        writer.start()
        reader.start()

    def write(self):
        while True:
            time.sleep(0.5)
            data = "CLIENT HI"
            self.sock.sendto(data.encode(), (self.addrinfo[4][0], self.MYPORT))

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
