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
        self.send_multicast_group = send_multicast_group
        self.send_udp_port = send_udp_port
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    def run(self):
        print("Starting server")
        self.dowork = True
        writer = threading.Thread(name='write', target=self.write)
        writer.start()

    def write(self):
        print("Starting to write to client")
        out = 'Hola'
        while self.dowork :
            self.send_sock.sendto(out.encode(), (self.send_multicast_group, self.send_udp_port))
            print("Sending: " + out)
        print("Stoping")
        self.send_sock.close()


parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to send changes in directory to a multicast group.')
parser.add_argument('-s','--send',dest='send_multicast',type=str, default="230.1.1.1", help='Multicast address to send data')
parser.add_argument('-i','--send_port',dest='send_port',type=int, default=5000, help='Multicast port to send data')

args = parser.parse_args()

serv = server(args.send_multicast, args.send_port)
serv.run()
