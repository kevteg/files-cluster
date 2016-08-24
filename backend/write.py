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
class server():
    def __init__(self, send_multicast_group, send_udp_port):
        #Setting udp socket to send information that comes through serial:
        group = 'ff05:70aa:aaaa:3333:4444:2222:1111:6666'
        self.addrinfo = socket.getaddrinfo(group, None)[0]
        self.send_sock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
        self.MYPORT = 8124
        # Set Time-to-live (optional)
        ttl_bin = struct.pack('@I', 1)
        self.send_sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)



    def run(self):
        print("Starting server")
        self.dowork = True
        writer = threading.Thread(name='write', target=self.write)
        writer.start()

    def write(self):
        print("Starting to write to client")
        while self.dowork :
            data = repr(time.time())
            self.send_sock.sendto(data.encode(), (self.addrinfo[4][0], self.MYPORT))
            time.sleep(1)
            print("Sending: " + data)
        print("Stoping")
        self.send_sock.close()


parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to send changes in directory to a multicast group.')
parser.add_argument('-s','--send',dest='send_multicast',type=str, default="230.1.1.1", help='Multicast address to send data')
parser.add_argument('-i','--send_port',dest='send_port',type=int, default=5000, help='Multicast port to send data')

args = parser.parse_args()

serv = server(args.send_multicast, args.send_port)
serv.run()
