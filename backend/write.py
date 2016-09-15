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
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify, GLib
# import ipaddress
'''
    Author: Keeeevin
    TODO: Write docs of each function
'''
class server():
    def __init__(self, group_name, username, dirc, interface = None):
        group, self.MYPORT = self.getConnectionInfo(group_name)
        self.directory = dirc
        self.interface = interface
        self.username = username
        self.time_to_send_list_of_files = 5#cada N segundos enviar lista de archivos en directorio
        self.send_list_of_files = False
        self.separator = '|'

        if group is not None:
            try:
                if directory.getFilesAtDirectory(self.directory) is None:
                    raise ValueError("That directory does not exist")
                print("Created IP: " + group + ", port: " + str(self.MYPORT))
                self.addrinfo = socket.getaddrinfo(group, self.MYPORT)[0]
                print(self.addrinfo)
                # Crea el socket del tipo IPv6
                self.multicast_sock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
                # se hace bind en ese puerto
                self.multicast_sock.bind(('', self.MYPORT))
                if self.interface is None:
                    interfaces = [i[1] for i in socket.if_nameindex() ]
                    for index, int in enumerate(interfaces, start = 0):
                        try:
                            if(index):
                                add = self.getOwnLinkLocal(int)
                                break
                        except:
                            continue
                    self.interface = int
                interface_index = socket.if_nametoindex(self.interface)
                # Unirse al grupo multicast
                group_bin = socket.inet_pton(self.addrinfo[0], self.addrinfo[4][0])
                mreq = struct.pack('@I', interface_index)
                self.multicast_sock.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_MULTICAST_IF, mreq)
                _group = socket.inet_pton(socket.AF_INET6, group) + mreq
                self.multicast_sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, _group)
                self.unicast_connected_to = {}
                self.unicast_connections = {}
                self.askForFiles = True
                self.count = True
                self.addInformationFile(group_name, self.username, self.interface, self.directory)
            except Exception as e:
                print("Error: ")
                print(e)
                exit(-1)
        else:
            print("Error: Select a name a bit larger please!", file=sys.stderr)
            exit(-1)

    def hello(self, notification, action_name, data):
        print("hello")

    def test(self):
        Notify.init("Hello there")
        Hello=Notify.Notification.new("Hello", "Do you want to delete this file xxx?.", "dialog-question")
        Hello.add_action(
            "action_click",
            "Reply to Message",
            self.hello,
            None
        )
        Hello.show()
        GLib.MainLoop().run()

    def addInformationFile(self, group_name, username, interface, directory):
        info = directory + ',' + group_name + ',' + username + ',' + interface
        user = subprocess.Popen('echo $USER', shell=True, stdout=subprocess.PIPE)
        add = True
        try:
            with open("/home/" + user.communicate()[0].decode('utf-8').replace("\n", "") + "/.files-cluster", "r") as f:
                for line in f.readlines():
                    if info == line.replace("\n", ""):
                        add = False
        except:
            pass
        if add:
            subprocess.Popen('echo \'' + info + '\' >> /home/$USER/.files-cluster', shell=True, stdout=subprocess.PIPE)

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
            # self.test = threading.Thread( name='test', target=self.test)
            # self.test.start()
            # self.test.join(1)
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
        if link_local == '':
            raise ValueError("No IPv6 address for that interface ")
        return link_local

    def compareIp(self, address):
        #Compares interfaces IP with the address, True if it exists
        try:
            connect_info = address.split('%') #interface and address
            link_local = self.getOwnLinkLocal(connect_info[1])
            return connect_info[0], connect_info[1], not(link_local == connect_info[0])
        except:
            raise ValueError("Error: could not find link local address")


    #This one connects to others socket
    def connectToTCPServer(self, name, address_to_connect, interface):
        try:
            time.sleep(1)
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            addr = socket.getaddrinfo(address_to_connect + '%' + interface, self.MYPORT - 10, socket.AF_INET6, 0, socket.SOL_TCP)[0]
            sock.connect(addr[-1])
            print ("Unicast connection with ", name)
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
        if send:
            self.sendToServer(server, message)
        try:
            while self.dowork:
                data = server.getSocket().recv(1024).decode().rstrip('\0').lstrip('\0') if not server.getReceiving() else server.getSocket().recv(1024)
                if not server.getReceiving():
                    print ('Received from ' + server.getUsername() + ':', repr(data))
                    information = data.split(self.separator)
                    try:
                        send, message = self.typeOfMessage(information[0], [True, server, information[1]])
                    except:
                        send = False
                        print("Error with received data")
                        self.deleteConnection(server)
                        self.doneReceiving([True])
                        break
                    if send:
                        self.sendToServer(server, message)
                else:
                    l = data
                    close = False
                    print("receiving as client")
                    while(l and not close):
                        try:
                            close = True if (l.decode().rstrip('\0').lstrip('\0').split(self.separator)[0] == "done") else False
                        except:
                            pass
                        if not close:
                            while l.endswith('\x00'):
                                l = l[:-1]
                            self.tmp.write(l)
                            l = server.getSocket().recv(1024)
                    server.setReceiving(False)
                    self.tmp.close()

        except Exception as e:
            print(e)
            self.dowork = False
        # print("chau")
        server.getSocket().close()

    def sendToServer(self, server, data, is_byte = False):
        if not is_byte:
            print ('Sending to ' + server.getUsername() + ':', repr(data))
            _s = int(1024 - len(data.encode()))
            data = (struct.pack(str(_s) + 'B',*([0]*_s))).decode() + data
        server.getSocket().send(data.encode() if not is_byte else data)

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
                data = client.getSocket().recv(1024).decode().rstrip('\0').lstrip('\0') if not client.getReceiving() else client.getSocket().recv(1024)
                if not client.getReceiving():
                    print("Receive from " + (client.getUsername() if client.getUsername() != "" else "client")+ ": ", repr(data))
                    information = data.split(self.separator)
                    try:
                        send, message = self.typeOfMessage(information[0].lstrip(' ').rstrip(' '), [True, client, information[1].lstrip(' ').rstrip(' ')])
                    except:
                        send = False
                        print("Error with received data")
                        self.deleteConnection(client)
                        self.doneReceiving([True])
                        break
                    if send:
                        self.sendToClient(client, message)
                else:
                    l = data
                    close = False
                    print("receiving as server")
                    while(l and not close):
                        try:
                            close = True if (l.decode().lstrip('\0').rstrip('\0').split(self.separator)[0] == "done") else False
                        except:
                            pass
                        if not close:
                            while l.endswith('\x00'):
                                l = l[:-1]
                            self.tmp.write(l)
                            l = client.getSocket().recv(1024)
                    client.setReceiving(False)
                    # print(l)
                    # try:
                    #     if l:
                    #         data = l.decode().rstrip('\0').lstrip('\0')
                    #         print(data)
                    #         information = data.split(':')
                    #         send, message = self.typeOfMessage(information[0].lstrip(' ').rstrip(' '), [True, client, information[1].lstrip(' ').rstrip(' ')])
                    # except Exception as e:
                    #     print(e)
                    print("no recibo mas de este archivo")
                    self.tmp.close()
        except Exception as e:
            print(e)
            self.tcp_socket.close()
            self.dowork = False

        client.getSocket().close()

    def sendToClient(self, client, data, is_byte = False):
        if not is_byte:
            print ('Sending to ' + client.getUsername() + ':', repr(data))
            _s = int(1024 - len(data.encode()))
            data = (struct.pack(str(_s) + 'B',*([0]*_s))).decode() + data
        client.getSocket().send(data.encode() if not is_byte else data)

    def processUnicastConnection(self, args):
        #Si la dirección es diferente a la propia
        #el primer args es si es o no unicast el segundo el que envia y el tercero la informacion
        if args:
            if not args[0]: #este mensaje llego desde multicast
                address_to_connect, interface, connect = self.compareIp(str(args[1][0]))
                if args is not None and not(connect):
                    print("I sent that UDP message!")
                else:
                    is_server, unicastObject = self.findUnicastObject(address_to_connect, interface)
                    if unicastObject is None:
                        print("I did not send that. Will create a unicast connection with " + address_to_connect)
                        self.connectToTCPServer(name = args[2], address_to_connect = address_to_connect, interface = interface)
                    else:
                        print("Already connected to " + args[2])

            else: #el mensaje llego desde unicast
                if args[1] is not None and args[1].getUsername() == "":
                    print("Changing client name to: " + args[2])
                    args[1].setUsername(args[2])

    def findUnicastObject(self, address, interface):
        uni_object = None
        is_server = False
        for uni in self.unicast_connected_to.keys():
            if uni.getAddress() == address + "%" + interface:
                uni_object = uni
                break
        if uni_object is None:
            for uni in self.unicast_connections.keys():
                if uni.getAddress() == address + "%" + interface:
                    uni_object = uni
                    is_server = True
                    break
        return is_server, uni_object

    def deleteConnection(self, obj):
        for uni in self.unicast_connected_to.keys():
            if uni.getAddress() == obj.getAddress():
                self.unicast_connected_to.pop(obj)
                break
        else:
            for uni in self.unicast_connections.keys():
                if uni.getAddress() == obj.getAddress():
                    self.unicast_connections.pop(obj)
                    break

    def isObjServer(self, obj):
        is_server = False
        for uni in self.unicast_connections.keys():
            if uni == obj:
                is_server = True
                break
        return is_server


    def sendFiles(self, args):
        #Args[1] a quien se le van a mandar los archivos
        #Args[2] archivos a enviar
        if args[0] and eval(args[2]) != []:
            is_server = self.isObjServer(args[1])
            # print("Sendddding: " + args[2])
            # print("Directory: " + self.directory)
            files = directory.getFilesObjects(self.directory, files = eval(args[2]))
            names = directory.getFilesAtDirectory(self.directory, needed_files = eval(args[2]),  add_path = False, extra = False)
            try:
                for index, _file in enumerate(files, start = 0):
                    self.sendToClient(args[1], "send" +self.separator + str(names[index]))
                    time.sleep(0.5)
                    l = _file.read(1024)
                    print("Sending..")
                    while(l):
                        _size = len(l)
                        # print(_size)
                        if _size < 1024:
                            _s = int(1024 - _size)
                            l = l + (struct.pack(str(_s) + 'B',*([0]*_s)))
                        # print(l)
                        if is_server:
                            self.sendToClient(args[1], l, is_byte = True)
                        else:
                            self.sendToServer(args[1], l, is_byte = True)
                        l = _file.read(1024)
                    if is_server:
                        self.sendToClient(args[1], "done" + self.separator + str(names[index]))
                        self.sendToClient(args[1], "done" + self.separator +"sending")
                    else:
                        self.sendToServer(args[1], "done" + self.separator + str(names[index]))
                        self.sendToServer(args[1], "done" + self.separator +"sending")
            except Exception as e:
                print("Error sending file")
                print(e)

    def receiveFile(self, args):
        if args[0]:
            self.askForFiles = False
            self.count = False
            #Aqui se borra o se decide que hacer con el archivo local
            self.tmp = open(self.directory + "/" + str(args[2]).strip(), "wb")
            args[1].setReceiving(True)

    def doneReceiving(self, args):
        if args[0]:
            print("DONE RECEIVING")
            self.askForFiles = True
            self.count = True

    def sendUserName(self, args):
        return 'connection' + self.separator + self.username

    def typeOfMessage(self, type, args = None):
        #retorna si va a responder y el mensaje que enviara si es que lo va a mandar
        methods =  {
            'greetings': (True, self.sendUserName),
            'connection': (False, self.processUnicastConnection),
            'list': (True, directory.getFilesAtDirectory),#Genera la lista de archivos
            'files': (False, self.checkFiles),#Revisa los archivos que están llegando
            'need': (False, self.sendFiles),#Archivos que necesita el otro host
            'send': (False, self.receiveFile),#Cambiar el estado del objeto para recibir archivos
            'done': (False, self.doneReceiving)
        }.get(type, (False, (lambda args: "Error")))
        return methods[0], methods[1](args)

    def checkFiles(self, args):
        # test_directory = "/tmp/empty2"
        if args and self.askForFiles:
            address_to_connect, interface, connect = self.compareIp(str(args[1][0]))
            user_files = eval(args[2])
            if not(connect):
                print("I sent that UDP message!")
            else:
                print("Check if I have those files")
                current_files = directory.getFilesAtDirectory(self.directory)
                current_files_names = [file[0] for file in current_files]
                current_files_size = [file[1] for file in current_files]
                current_files_date = [file[2] for file in current_files]
                petition = []

                for _file in user_files:
                    if _file[0] in current_files_names:
                        for file in current_files:
                            if file[0] == _file[0]:
                                if int(file[1]) != int(_file[1]) and time.strptime(file[2], "%a %b %d %H:%M:%S %Y") < time.strptime(_file[2], "%a %b %d %H:%M:%S %Y"):
                                    petition.append(_file)
                                    break
                    else:
                        petition.append(_file)

                if petition != []:
                    print("Gonna ask for: ")
                    print(petition)
                    is_server, unicastObject = self.findUnicastObject(address_to_connect, interface)
                    if unicastObject:
                        if is_server:
                            self.sendToClient(unicastObject, "need" + self.separator + str(petition))
                        else:
                            self.sendToServer(unicastObject, "need" + self.separator + str(petition))
                    else:
                        print("Not connected to that host yet")

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
                information = data.decode('utf-8').split(self.separator)
                try:
                    send, message = self.typeOfMessage(information[0], [False, sender, information[1]])
                    if send:
                        self.sendToGroup(message)
                except:
                    print("Error with received data")
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
                if self.count and send_files_count_secs > self.time_to_send_list_of_files:
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
                        self.sendToGroup("files" + self.separator + str(message))
        except (KeyboardInterrupt, SystemExit):
            self.dowork = False



parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to receive changes in directory to a multicast group.')
parser.add_argument('-g','--group', required = True, dest='group_name',type=str, help='Group to connect in')
parser.add_argument('-n','--name', required = True, dest='username',type=str, help='User name')
parser.add_argument('-i','--interface', required = False, default = None, dest='interface',type=str, help='Interface to use')
parser.add_argument('-d','--directory', required = True, dest='directory',type=str, help='Directory to share')

args = parser.parse_args()
serv = server(group_name = args.group_name, username = args.username, interface =args.interface, dirc =  args.directory)
serv.run()
