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
from unicast_obj import uniObj
import directory
'''
    Author: Keeeevin
    TODO: Write docs of each function
'''
class server():
    def __init__(self, group_name, username, interface, dirc):
        group, self.MYPORT = self.getConnectionInfo(group_name)
        self.directory = dirc
        self.time_to_send_list_of_files = 5#cada N segundos enviar lista de archivos en directorio
        self.send_list_of_files = False
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
        try:
            print("Starting files-cluster")
            self.dowork = True
            self.multicast_thread = threading.Thread(name='multicast_check', target=self.multicast_check)
            self.tcp_thread = threading.Thread( name='tcp_thread', target=self.waitTCPCLients, args=[self.interface])
            self.multicast_thread_sender = threading.Thread( name='multicast_sender', target=self.multicast_sender)
            self.time_check = threading.Thread( name='time_check', target=self.time_checker)
            self.time_check.start()
            self.time_check.join(1)
            self.multicast_thread.start()
            self.multicast_thread.join(1)
            self.multicast_thread_sender.start()
            self.multicast_thread_sender.join(1)
            # while True:
            #     pass
        except (KeyboardInterrupt, SystemExit):
            print("Turnning off files-cluster")
            self.multicast_sock.close()
            self.dowork = False

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
            return "", "", False


    #This one connects to others socket
    def connectToTCPServer(self, name, address_to_connect, interface):
        try:
            time.sleep(1)
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            addr = socket.getaddrinfo(address_to_connect + '%' + interface, self.MYPORT - 10, socket.AF_INET6, 0, socket.SOL_TCP)[0]
            sock.connect(addr[-1])
            print ("Unicast connection with ", name)
            print (addr[-1][0])
            #Este diccionario contiene todos los hilos que manejan los sockets de los clientes
            new_server = uniObj(username = name, socket = sock, address = addr[-1][0])
            self.unicast_connected_to[new_server] = threading.Thread(daemon=True, name='tcpConnectedTo'+name, target=self.tcpConnectedTo, args=[new_server])
            self.unicast_connected_to[new_server].start()
            # self.unicast_connected_to[new_server].join(1)
        except Exception as e:
            print(e)
            print("User " + name + " seems to not be listening :(")

    #Este es el método del hilo que maneja el socket de conexión cuando se es cliente
    def tcpConnectedTo(self, server):
        #El primer mensaje deberia ser un saludo
        send, message = self.typeOfMessage('greetings')
        while send:
            time.sleep(1)
            self.sendToServer(server, message)
        try:
            while self.dowork:
                data = server.getSocket().recv(1024).decode()
                print ('Received from ' + server.getUsername() + ':', repr(data))
        except (KeyboardInterrupt, SystemExit):
            self.dowork = False
        # print("chau")
        server.getSocket().close()

    def sendToServer(self, server, data):
        print ('Sending to ' + server.getUsername() + ':', repr(data))
        server.getSocket().send(data.encode())

    #This one creates own tcp socket
    #aqui deberian ir la asignación de los hilos
    def waitTCPCLients(self, interface):
        # interface = "vmnet1"
        addr = socket.getaddrinfo(self.getOwnLinkLocal(interface) + '%' + interface, self.MYPORT - 10, socket.AF_INET6, 0, socket.SOL_TCP)[0]
        self.tcp_socket = socket.socket(addr[0], socket.SOCK_STREAM)
        self.tcp_socket.bind(addr[-1])
        self.tcp_socket.listen(10)
        print ("Server opened socket connection: ", self.tcp_socket, ", address: '%s'" % str(addr[-1]))
        try:
            while self.dowork:
                conn, address = self.tcp_socket.accept()
                print("Connection stablished with " + str(address))
                #el primer mensaje deberia ser el nombre
                new_client = uniObj(socket = conn, address = str(address[0]))
                self.unicast_connections[new_client] = threading.Thread(name='tcpConnection'+new_client.getAddress(), target=self.tcpConnection, args=[new_client])
                self.unicast_connections[new_client].start()
                self.unicast_connections[new_client].join(1)
        except (KeyboardInterrupt, SystemExit):
            self.tcp_socket.close()
            self.dowork = False
        self.tcp_socket.close()

    #Este es el método del hilo que maneja el socket de conexión cuando se es servidor
    def tcpConnection(self, client):
        try:
            while self.dowork:
                data = client.getSocket().recv(1024)
                print("Receive from " + (client.getUsername() if client.getUsername() != "" else "client")+ ": ", data)
                #Aqui se procesa ese mensaje
                information = data.decode('utf-8').split(':')
                self.sendToClient(client, data)
                send, message = self.typeOfMessage(information[0], [True, client, information[1]])
                if send:
                    self.sendToClient(client, message)
                print(client.getUsername())
        except (KeyboardInterrupt, SystemExit):
            self.tcp_socket.close()
            self.dowork = False

        client.getSocket().close()

    def sendToClient(self, client, data):
        client.getSocket().send(data)

    def processUnicastConnection(self, args):
        #Si la dirección es diferente a la propia
        #el primer args es si es o no unicast el segundo el que envia y el tercero la informacion
        if args:
            if not args[0]: #este mensaje llego desde multicast
                address_to_connect, interface, connect = self.compareIp(str(args[1][0]))
                if args is not None and not(connect):
                    print("I sent that UDP message!")
                else:
                    #revisar si ya esta esa conexión
                    print("I did not send that. Will create a unicast connection with " + address_to_connect)
                    self.connectToTCPServer(name = args[2], address_to_connect = address_to_connect, interface = interface)
            else: #el mensaje llego desde unicast
                if args[1] is not None and args[1].getUsername() != "":
                    print("Ahora le pondre nombre a " + args[2])
                    args[1].setUsername(args[2])


    def sendUserName(self, args):
        return 'connection: ' + self.username

    def typeOfMessage(self, type, args = None):
        #retorna si va a responder y el mensaje que enviara al grupo
        methods =  {
            'greetings': (True, self.sendUserName),
            'connection': (False, self.processUnicastConnection),
            'list': (True, directory.getFilesAtDirectory),
            'files': (False, self.checkFiles),
        }.get(type, (False, (lambda args: "Error")))
        return methods[0], methods[1](args)

    def checkFiles(self, args):
        # test_directory = "/tmp/empty2"
        if args:
            address_to_connect, interface, connect = self.compareIp(str(args[1][0]))
            user_files = eval(args[2])

            if args is not None and not(connect):
                print("I sent that UDP message!")
            else:
                print("Check if I have those files")
                current_files = directory.getFilesAtDirectory(self.directory)
                petition = []
                print("receiving: ")
                print(user_files)
                for _file in user_files:
                    if _file not in current_files:
                        petition.append(_file)
                print("Gonna ask for:")
                print(petition)
                #Trabajar en la parte de tcp

    def sendToGroup(self, message):
        print("Sending to group: " + message)
        self.multicast_sock.sendto(message.encode(), (self.addrinfo[4][0], self.MYPORT))

    def multicast_check(self):
        #mensaje de saludo inicial a los que esten escuchando
        #este método se encarga de responder a lo que llegue
        send, message = self.typeOfMessage('greetings')
        if send:
            self.tcp_thread.start()
            self.sendToGroup(message)
        try:
            while self.dowork:
                data, sender = self.multicast_sock.recvfrom(1500)
                while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
                print (str(sender) + ' ' + repr(data))
                information = data.decode('utf-8').split(':')
                send, message = self.typeOfMessage(information[0], [False, sender, information[1]])
                if send:
                    self.sendToGroup(message)
        except (KeyboardInterrupt, SystemExit):
            self.multicast_sock.close()
            self.dowork = False
        self.multicast_sock.close()

    def time_checker(self):
        send_files_count_secs = 0
        try:
            while self.dowork:
                time.sleep(1)
                send_files_count_secs = send_files_count_secs + 1
                if send_files_count_secs > self.time_to_send_list_of_files:
                    self.send_list_of_files = True
                    send_files_count_secs = 0
        except (KeyboardInterrupt, SystemExit):
            self.dowork = False

    def multicast_sender(self):
        #este método se encarga de enviar información sin petición
        try:
            while self.dowork:
                if self.send_list_of_files:
                    self.send_list_of_files = False
                    send, message = self.typeOfMessage('list', self.directory)
                    if send:
                        self.sendToGroup("files: " + str(message))
        except (KeyboardInterrupt, SystemExit):
            self.dowork = False



parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to receive changes in directory to a multicast group.')
parser.add_argument('-g','--group', required =True, dest='group_name',type=str, help='Group to connect in')
parser.add_argument('-n','--name', required =True, dest='username',type=str, help='User name')
parser.add_argument('-i','--interface', required =True, dest='interface',type=str, help='Interface to use')
parser.add_argument('-d','--directory', required =True, dest='directory',type=str, help='Directory to share')

args = parser.parse_args()
serv = server(args.group_name, args.username, args.interface, args.directory)
serv.run()
