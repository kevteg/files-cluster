#!/usr/bin/env python
# -*- coding: utf-8 -*
import time
import socket
import threading
import struct
import os
import argparse
import binascii
# from sendfile import sendfile
'''
    Author: Keeeevin
'''
class server():
    def __init__(self, group_name):
        #Setting udp socket to send information that comes through serial:
        # group, self.MYPORT = self.getConnectionInfo(group_name)
        # print("Created IP: " + group + ", port " + str(self.MYPORT))
        # self.addrinfo = socket.getaddrinfo(group, None)[0]
        # self.send_sock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
        # # Set Time-to-live (optional)
        # ttl_bin = struct.pack('@I', 1)
        # self.send_sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
        group, self.MYPORT = self.getConnectionInfo(group_name)
        print("Created IP: " + group + ", port: " + str(self.MYPORT))
        self.addrinfo = socket.getaddrinfo(group, None)[0]
        # Create a socket
        self.sock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
        self.sock.bind(('', self.MYPORT))
        group_bin = socket.inet_pton(self.addrinfo[0], self.addrinfo[4][0])
        mreq = group_bin + struct.pack('@I', 0)
        # ttl_bin = struct.pack('@I', 1)
        # self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
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
        print("Starting server")
        self.dowork = True
        self.writer = threading.Thread(name='write', target=self.write)
        reader = threading.Thread(name='read', target=self.read)
        reader.start()
        self.writer.start()
        # self.writer.start()
    def read(self):
        while True:
            data, sender = self.sock.recvfrom(1500)
            while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
            print (str(sender) + ' ' + repr(data))

    def write(self):
        print("Starting to write to client")
        # file = open("somefile", "rb")
        while self.dowork:
            data = repr(time.time())
            self.sock.sendto(data.encode(), (self.addrinfo[4][0], self.MYPORT))
            time.sleep(1)
            print("Sending: " + data)
        print("Stoping")
        self.sock.close()



parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to receive changes in directory to a multicast group.')
parser.add_argument('-g','--group',dest='group_name',type=str, help='Group to connect in')

args = parser.parse_args()

serv = server(args.group_name)
serv.run()
