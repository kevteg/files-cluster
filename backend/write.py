#!/usr/bin/env python
# -*- coding: utf-8 -*
import time
import socket
import threading
import struct
import os
import argparse
import binascii
import subprocess
# from sendfile import sendfile
'''
    Author: Keeeevin
'''
class server():
    def __init__(self, group_name, username):
        group, self.MYPORT = self.getConnectionInfo(group_name)
        # group = "fe80::351d:ce3:a858:f551"
        print("Created IP: " + group + ", port: " + str(self.MYPORT))
        # print(socket.getaddrinfo(group, None))
        self.addrinfo = socket.getaddrinfo(group, None)[0]
        self.username = username
        # Crea el socket del tipo IPv6
        self.multicast_sock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
        # se hace bind en ese puerto
        self.multicast_sock.bind(('', self.MYPORT))
        group_bin = socket.inet_pton(self.addrinfo[0], self.addrinfo[4][0])
        mreq = group_bin + struct.pack('@I', 0)
        # ttl_bin = struct.pack('@I', 1)
        # self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
        self.multicast_sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)


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
        self.reader = threading.Thread(name='read', target=self.read)
        self.multicast_thread = threading.Thread(name='multicast_check', target=self.multicast_check)
        # self.writer.start()
        # self.reader.start()
        self.multicast_thread.start()

    def read(self):
        while self.dowork:
            data, sender = self.multicast_sock.recvfrom(1500)
            while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
            print (str(sender) + ' ' + repr(data))

    def write(self):
        print("Starting to write to client")
        # file = open("somefile", "rb")
        while self.dowork:
            data = repr(time.time())
            self.multicast_sock.sendto(data.encode(), (self.addrinfo[4][0], self.MYPORT))
            time.sleep(1)
            print("Sending: " + data)
        print("Stoping")
        self.multicast_sock.close()

    def compareIp(self, address):
        #Compares interfaces IP with the address, True if it exists
        try:
            connect_info = address.split('%') #interface and address
            find_ip = subprocess.Popen('ip addr show ' + connect_info[1] + ' | grep "\<inet6\>" | awk \'{ print $2 }\' | awk \'{ print $1 }\'', shell=True, stdout=subprocess.PIPE)
            link_local = str(find_ip.communicate()[0].decode('utf-8')).split('/')[0]
            return (link_local == connect_info[0])
        except:
            print("Terrible error")
            return False
    def createUnicast(self, args):
        #Si la dirección es diferente a la propia
        if args is not None and self.compareIp(str(args[0])):
            print("I sent that message!")


    def sendUserName(self, args):
        return 'connection: ' + self.username

    def typeOfMessage(self, type, args = None):
        #retorna si va a responder y el mensaje que enviara al grupo
        methods =  {
            'greetings': (True, self.sendUserName),
            'connection': (False, self.createUnicast),
        }.get(type, (False, (lambda args: "Error")))
        return methods[0], methods[1](args)

    def sendToGroup(self, message):
        print("Sending to group: " + message)
        # print(self.multicast_sock.gethostbyname())
        self.multicast_sock.sendto(message.encode(), (self.addrinfo[4][0], self.MYPORT))

    def multicast_check(self):
        #mensaje de saludo inicial a los que esten escuchando
        send, message = self.typeOfMessage('greetings')
        if send:
            self.sendToGroup(message)

        while self.dowork:
            data, sender = self.multicast_sock.recvfrom(1500)
            while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
            print (str(sender) + ' ' + repr(data))
            send, message = self.typeOfMessage(data.decode('utf-8').split(':')[0], sender)
            if send:
                print("Sending " + message)
                self.multicast_sock.sendto(message.encode(), (self.addrinfo[4][0], self.MYPORT))

        self.multicast_sock.close()

parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to receive changes in directory to a multicast group.')
parser.add_argument('-g','--group', required =True, dest='group_name',type=str, help='Group to connect in')
parser.add_argument('-n','--name', required =True, dest='username',type=str, help='User name')

args = parser.parse_args()

serv = server(args.group_name, args.username)
serv.run()
