#!/usr/bin/env python3
# -*- coding: utf-8 -*
import time
import socket
import threading
import struct
import os
import argparse
import binascii
import subprocess
import sys
import unicast_obj
# from sendfile import sendfile
'''
    Author: Keeeevin
    TODO: Write docs of each function
'''
class server():
    def __init__(self, group_name, username, interface):
        group, self.MYPORT = self.getConnectionInfo(group_name)
        if group is not None:
            try:
                self.interface = interface
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
                self.unicast_connected_to = {}
                self.unicast_connections = {}
            except Exception as e:
                print("Error: Is IPv6 activated?", file=sys.stderr)
                print(e)
                exit(-1)
        else:
            print("Error: Select a name a bit larger please!", file=sys.stderr)
            exit(-1)

    def getConnectionInfo(self, group_name):
        ip = None
        port = None
        if len(group_name) > 5:
            text = (binascii.hexlify(group_name.encode('utf-8')).decode())
            port = int('0x' + text[len(text) - 4:len(text)], 0)
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
        self.multicast_thread = threading.Thread(name='multicast_check', target=self.multicast_check)
        self.tcp_thread = threading.Thread(name='tcp_thread', target=self.waitTCPCLients, args=[self.interface])
        self.multicast_thread.start()

    def getOwnLinkLocal(self, interface):
        find_ip = subprocess.Popen('ip addr show ' + interface + ' | grep "\<inet6\>" | awk \'{ print $2 }\' | awk \'{ print $1 }\'', shell=True, stdout=subprocess.PIPE)
        link_local = str(find_ip.communicate()[0].decode('utf-8')).split('/')[0]
        return link_local

    def compareIp(self, address):
        #Compares interfaces IP with the address, True if it exists
        try:
            connect_info = address.split('%') #interface and address
            link_local = self.getOwnLinkLocal(connect_info[1])
            return connect_info[0], connect_info[1], not(link_local == connect_info[0])
        except:
            print("Error: could not find link local address", file=sys.stderr)
            return "", False


    #This one connects to others socket
    def connectToTCPServer(self, name, address_to_connect, interface):
        try:
            time.sleep(1)
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            addr = socket.getaddrinfo(address_to_connect + '%' + interface, self.MYPORT - 20, socket.AF_INET6, 0, socket.SOL_TCP)[0]
            sock.connect(addr[-1])
            print ("Unicast connection with ", name)
            #Este diccionario contiene todos los hilos que manejan los sockets de los clientes
            self.unicast_connected_to[name] = threading.Thread(name='tcpConnectedTo'+name, target=self.tcpConnectedTo, args=[sock])
            self.unicast_connected_to[name].start()
        except Exception as e:
            print(e)
            print("User " + name + " seems to not be listening :(")

    #Este es el método del hilo que maneja el socket de conexión cuando se es cliente
    def tcpConnectedTo(self, sock):
        #El primer mensaje deberia ser un saludo
        data = 'Hello, world! -> via IPv6 :-)'
        print ('Client is sending:', repr(data))
        #Crear un diccionario de las conecciones y sus direcciones o sus sockets
        sock.send(data.encode())
        data = sock.recv(1024).decode()
        print ('Client received response:', repr(data))
        sock.close()

    #This one creates own tcp socket
    #aqui deberian ir la asignación de los hilos
    def waitTCPCLients(self, interface):
        # interface = "vmnet1"
        addr = socket.getaddrinfo(self.getOwnLinkLocal(interface) + '%' + interface, self.MYPORT - 10, socket.AF_INET6, 0, socket.SOL_TCP)[0]
        self.tcp_socket = socket.socket(addr[0], socket.SOCK_STREAM)
        self.tcp_socket.bind(addr[-1])
        self.tcp_socket.listen(10)
        print ("Server opened socket connection:", self.tcp_socket, ", address: '%s'" % str(addr[-1]))
        conn, address = self.tcp_socket.accept()
        print("Connection stablished with " + str(address))
        #el primer mensaje deberia ser el nombre
        self.unicast_connections[str(address[0])] = threading.Thread(name='tcpConnection'+str(address[0]), target=self.tcpConnection, args=[conn])
        self.unicast_connections[str(address[0])].start()

    #Este es el método del hilo que maneja el socket de conexión cuando se es servidor
    def tcpConnection(self, conn):
        if True: # answer a single request
            data = conn.recv(1024)
            conn.send(data)
        conn.close()


    def createUnicast(self, args):
        #Si la dirección es diferente a la propia
        if args:
            address_to_connect, interface, connect = self.compareIp(str(args[0][0]))
            if args is not None and not(connect):
                print("I sent that UDP message!")
            else:
                #revisar si ya esta esa conexión
                print("I did not sent that. Will create a unicast connection with " + address_to_connect)
                self.connectToTCPServer(name = args[1], address_to_connect = address_to_connect, interface = interface)

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
            self.tcp_thread.start()
            self.sendToGroup(message)

        while self.dowork:
            data, sender = self.multicast_sock.recvfrom(1500)
            while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
            print (str(sender) + ' ' + repr(data))
            information = data.decode('utf-8').split(':')
            send, message = self.typeOfMessage(information[0], [sender, information[1]])
            if send:
                self.sendToGroup(message)

        self.multicast_sock.close()

parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to receive changes in directory to a multicast group.')
parser.add_argument('-g','--group', required =True, dest='group_name',type=str, help='Group to connect in')
parser.add_argument('-n','--name', required =True, dest='username',type=str, help='User name')
parser.add_argument('-i','--interface', required =True, dest='interface',type=str, help='Interface to use')

args = parser.parse_args()

serv = server(args.group_name, args.username, args.interface)
serv.run()
