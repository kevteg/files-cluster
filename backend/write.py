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
                Notify.init("File notification")
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
                self.self_obj = uniObj(username = username)
                self.is_sending = False #Para saber si Está mandando un archivo
                self.addInformationFile(group_name, self.username, self.interface, self.directory)
            except Exception as e:
                print("Error: ", file=sys.stderr)
                print(e, file=sys.stderr)
                exit(-1)
        else:
            print("Error: Select a name a bit larger please!", file=sys.stderr)
            exit(-1)

    '''
    brief: Método que muestra que el usuario se fue
    param: message:     Mensaje a mostrar al usuario
    '''
    def userGone(self, message):
        file_change=Notify.Notification.new("Hola", message, "dialog-question")
        file_change.show()
        try:
            GLib.MainLoop().run()
        except:
            return True
    '''
    brief: Método que muestra una ventana de confirmación para borrar los archivos que otro usuario borro
    param: message:     Mensaje a mostrar al usuario
           files:     Archivos a borrar en caso de que el usuario acepte
    '''
    def delete(self, message, files):

        file_change=Notify.Notification.new("Hello", message, "dialog-question")
        file_change.add_action(
            "action_click",
            "¡Si!",
            self.acceptMessage,
            files
        )
        file_change.show()
        try:
            GLib.MainLoop().run()
        except:
            return True
    '''
    brief: Método que se llama si un user decide eliminar los archivos que alguien más borro
    param: notification:     notificación que llama al método
           action_name: nombre de la acción
           files: archivos a borrar
    '''
    def acceptMessage(self, notification, action_name, files):
        print("Gonna delete these files:")
        for f in files:
            try:
                print("Deleting: " + f)
                os.remove(self.directory + "/" + f)
                print("Done")
            except:
                pass

    '''
    brief: Método que genera un log sobre los directorios que se han compartido
    param: group_name:     nombre del grupo del script
           username:     nombre de para identificar al usuario
           interfaz:     interfaz con la que se conectó el script
    '''
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
    '''
    brief: Método que genera una dirección multicast y un puerto en base al nombre de grupo que escogio el user
    param: group_name:     nombre del grupo del script
    return: dirección y puerto multicast a conectar
    '''
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
    '''
   brief: Método que corre los hilos principales de la aplicación
   '''
    def run(self):
        try:
            print("Starting files-cluster")
            self.dowork = True
            self.multicast_thread = threading.Thread(name='multicast_check', target=self.multicast_check)
            self.tcp_thread = threading.Thread( name='tcp_thread', target=self.waitTCPCLients, args=[self.interface])
            self.multicast_thread_sender = threading.Thread( name='multicast_sender', target=self.multicast_sender)
            self.time_check = threading.Thread( name='time_check', target=self.time_checker)
            self.listen_to_stdin = threading.Thread( name='userInput', target=self.userInput)
            self.listen_to_stdin.start()
            self.listen_to_stdin.join(1)
            self.time_check.start()
            self.time_check.join(1)
            self.multicast_thread.start()
            self.multicast_thread.join(1)
            self.multicast_thread_sender.start()
            self.multicast_thread_sender.join(1)
        except (KeyboardInterrupt, SystemExit):
            print("Turnning off files-cluster")
            self.multicast_sock.close()
            self.dowork = False
    '''
    brief: Método que retorna la dirección de enlace local de la interfaz
    param: interface: interfaz donde se buscará la dirección de enlance local
    return: dirección de enlace local de la interfaz recibida
    '''
    def getOwnLinkLocal(self, interface):
        find_ip = subprocess.Popen('ip addr show ' + interface + ' | grep "\<inet6\>" | awk \'{ print $2 }\' | awk \'{ print $1 }\'', shell=True, stdout=subprocess.PIPE)
        link_local = str(find_ip.communicate()[0].decode('utf-8')).split('/')[0]
        if link_local == '':
            raise ValueError("Error: No IPv6 address for that interface ")
        return link_local
    '''
    brief: Método que compara la dirección local con otra
    param: address: dirección a comparar
    return: interfaz, ip y si es la misma dirección local
    '''
    def compareIp(self, address):
        try:
            connect_info = address.split('%') #interface and address
            link_local = self.getOwnLinkLocal(connect_info[1])
            return connect_info[0], connect_info[1], not(link_local == connect_info[0])
        except:
            raise ValueError("Error: could not find link local address")

    '''
    brief: Método que conecta a otro equipo como cliente (unicast)
    param: address_to_connect: dirección a conectar
           name: nombre del usuario al que se va a conectar
           interface: interfaz por donde conectarse
    '''
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
            print(e, file=sys.stderr)
            print("User " + name + " seems to not be listening :(")

    #Este es el método del hilo que maneja el socket de conexión cuando se es cliente
    '''
    brief: Método que tiene cada hilo de conexión cuando se es cliente
    param: server: socket del otro usuario
    '''
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
                        self.userGone("El usuario " + server.getUsername() + "(" + self.directory + ")" + " se ha ido")
                        self.doneReceiving([True])
                        break
                    if send:
                        self.sendToServer(server, message)
                else:
                    l = data
                    close = False
                    # counter = 1
                    print("receiving as client")
                    while(l and not close):
                        try:
                            close = True if (l.decode().rstrip('\0').lstrip('\0').split(self.separator)[0] == "done") else False
                        except:
                            pass
                        if not close:
                            # if counter >= self.portion:
                            #     try:
                            #         while l.endswith(b'\x00'):
                            #             l = l[:-1]
                            #     except Exception as e:
                            #         pass
                            self.tmp.write(l)
                            l = server.getSocket().recv(1024)
                    server.setReceiving(False)
                    self.tmp.close()

        except Exception as e:
            print(e)
            self.dowork = False
        # print("chau")
        server.getSocket().close()

    '''
    brief: Método que envia por unicast a un objeto servidor
    param: server: servidor a quien se le enviara los datos
           data: datos a enviar
           is_byte: indica si data está en bytes o no
    '''
    def sendToServer(self, server, data, is_byte = False):
        if not is_byte:
            print ('Sending to ' + server.getUsername() + ':', repr(data))
            _s = int(1024 - len(data.encode()))
            data = (struct.pack(str(_s) + 'B',*([0]*_s))).decode() + data
        server.getSocket().send(data.encode() if not is_byte else data)

    '''
    brief: Método que espera las conexiones de clientes y asigna un hilo para manejar dicha conexión
    param: interface: interfaz de conexión
    '''
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

    '''
    brief: Método que tiene cada hilo de conexión cuando se es servidor
    param: client: socket del otro usuario
    '''
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
                        self.userGone("El usuario " + client.getUsername() + " (" + self.directory + ")" + " se ha ido")
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
                            self.tmp.write(l)
                            l = client.getSocket().recv(1024)
                    client.setReceiving(False)
                    self.tmp.close()
        except Exception as e:
            print(e)
            self.tcp_socket.close()
            self.dowork = False

        client.getSocket().close()
    '''
    brief: Método que envia por unicast a un objeto cliente
    param: client: cliente a quien se le enviara los datos
           data: datos a enviar
           is_byte: indica si data está en bytes o no
    '''
    def sendToClient(self, client, data, is_byte = False):
        if not is_byte:
            print ('Sending to ' + client.getUsername() + ':', repr(data))
            _s = int(1024 - len(data.encode()))
            data = (struct.pack(str(_s) + 'B',*([0]*_s))).decode() + data
        client.getSocket().send(data.encode() if not is_byte else data)

    '''
    brief: Método que procesa el saludo de los hosts que se conecten al grupo multicast y crea una conexión unicast con ellos
    param: args: argumentos del método
    '''
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

    '''
    brief: Método que busca el objeto unicast asociado a una dirección
    param: address: dirección del objeto que se busca
           interface: interfaz de la conexión
    '''
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
    '''
    brief: Método que elimina las conexiones unicast
    param: obj: objeto a eliminar
    '''
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
    '''
    brief: Método que indica si el objeto unicast es servidor
    param: obj: objeto a verificar
    '''
    def isObjServer(self, obj):
        is_server = False
        for uni in self.unicast_connections.keys():
            if uni == obj:
                is_server = True
                break
        return is_server

    '''
    brief: Método que envia por unicast los archivos a un user
    param: args: argumentos del método, incluyendo la petición de archivos y el objeto unicast que lo pidio
    '''
    def sendFiles(self, args):
        #Args[1] a quien se le van a mandar los archivos
        #Args[2] archivos a enviar
        if args[0] and eval(args[2]) != []:
            is_server = self.isObjServer(args[1])
            files = directory.getFilesObjects(self.directory, files = eval(args[2]))
            names = directory.getFilesAtDirectory(self.directory, needed_files = eval(args[2]),  add_path = False, extra = False)
            try:
                if not self.is_sending:
                    self.is_sending = True
                    for index, _file in enumerate(files, start = 0):
                        self.sendToClient(args[1], "send" + self.separator + str(names[index]))
                        l = _file.read(1024)
                        print("Sending..")
                        while(l):
                            _size = len(l)
                            if _size < 1024:
                                _s = int(1024 - _size)
                                l = l + (struct.pack(str(_s) + 'B',*([0]*_s)))
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
                        _file.close()
                    self.is_sending = False
            except Exception as e:
                print("Error sending file")
                print(e)
    '''
    brief: Método que crea el archivo vacio y prepara al script para no pedir mas archivos a nadie
    param: args: argumentos del método
    '''
    def receiveFile(self, args):
        if args[0]:
            self.askForFiles = False
            self.count = False
            # size_of_comming_file = eval(args[2])[1]
            # self.portion = size_of_comming_file/1024
            self.tmp = open(self.directory + "/" + str(args[2]).strip(), "wb")
            args[1].setReceiving(True)
    '''
    brief: Método que se llama al recibir un donde sending del objeto unicast
    param: args: en este caso se usa para verificar que es unicast la conexión
    '''
    def doneReceiving(self, args):
        if args[0]:
            print("DONE RECEIVING")
            self.askForFiles = True
            self.count = True
    '''
    brief: Método que envia el saludo inial
    param: args: argumentos del método, en este caso no es necesario
    return: nombre al grupo multicast
    '''
    def sendUserName(self, args):
        return 'connection' + self.separator + self.username
    '''
    brief: Método que actua como un multiplexor de las diferentes peticiones que se reciban, envia la información al método correcto, por eso todos reciben args
    param: type: petición que hace el otro programa
           args: argumentos a mandar al script
    '''
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

    '''
    brief: Método que revisa los archivos que envian los programas al grupo y decide si pedirlos o no
    param: args: argumentos del método
    '''
    def checkFiles(self, args):
        if args and self.askForFiles:
            address_to_connect, interface, connect = self.compareIp(str(args[1][0]))
            user_files = eval(args[2])
            if not(connect):
                print("I sent that UDP message!")
            else:
                print("Check if I have those files")
                try:
                    petition = []
                    current_files = directory.getFilesAtDirectory(self.directory)
                    current_files_names = [file[0] for file in current_files]
                    is_server, partner_connection = self.findUnicastObject(address = address_to_connect, interface = interface)
                    if partner_connection:
                        partner_connection.setFileList(user_files)
                        files_to_delete = [mfile for mfile in current_files_names if mfile in partner_connection.getNotAskFor()]

                        if files_to_delete != []:
                            message_to_user = "El usuario: " + partner_connection.getUsername() + "(" + self.directory +  ")" + " borro: " + ", ".join(files_to_delete) + "\n ¿Quieres borrarlo también?"
                            notification = threading.Thread( name='notification', target=self.delete, args = [message_to_user, files_to_delete])
                            notification.start()
                            notification.join(1)

                        self.self_obj.setFileList(current_files)
                        for _file in user_files:
                            if _file[0] in current_files_names:
                                for file in current_files:
                                    if file[0] == _file[0]:
                                        if int(file[1]) != int(_file[1]) and time.strptime(file[2], "%a %b %d %H:%M:%S %Y") < time.strptime(_file[2], "%a %b %d %H:%M:%S %Y"):
                                            petition.append(_file)
                                            break
                            elif _file[0] not in self.self_obj.getNotAskFor():
                                petition.append(_file)
                        partner_connection.resetNotAskFor()
                    else:
                        print("Not connected to that host yet")
                except Exception as e:
                    print(e)

                if petition != []:
                    print("Gonna ask for: ")
                    print(petition)
                    if partner_connection:
                        if is_server:
                            self.sendToClient(partner_connection, "need" + self.separator + str(petition))
                        else:
                            self.sendToServer(partner_connection, "need" + self.separator + str(petition))

    '''
    brief: Método que envia mensajes al grupo multicast
    param: message: mensaje a enviar
    '''
    def sendToGroup(self, message):
        print("Sending to group: " + message)
        self.multicast_sock.sendto(message.encode(), (self.addrinfo[4][0], self.MYPORT))
    '''
    brief: Método que se mantiene escuchando el grupo multicast, también envia el mensaje inicial
    '''
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

    '''
    brief: Método cuenta los segundos para enviar información de los archivos al grupo multicast
    '''
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
    '''
    brief: Método que envia al grupo multicast
    '''
    def multicast_sender(self):
        #este método se encarga de enviar información sin petición
        try:
            while self.dowork:
                if self.send_list_of_files:
                    self.send_list_of_files = False
                    send, message = self.typeOfMessage('list', self.directory)
                    if send:
                        self.self_obj.setFileList(eval(str(message)))
                        self.sendToGroup("files" + self.separator + str(message))
        except (KeyboardInterrupt, SystemExit):
            self.dowork = False
    '''
    brief: Método que cierra todas las conexiones iniciales
    '''
    def killEverySocket(self):
        for uni in self.unicast_connected_to.keys():
            uni.getSocket().close()
        for uni in self.unicast_connections.keys():
            uni.getSocket().close()
    '''
    brief: Método que escucha el input del user para cerrar el programa
    '''
    def userInput(self):
        while self.dowork:
            _in = input()
            if(_in == "exit"):
                self.dowork = False
                self.multicast_sock.close()
                self.tcp_socket.close()
                self.killEverySocket()
                GLib.MainLoop().quit()
                print("You may close me now")
                exit(0)


parser = argparse.ArgumentParser(prog='serialserver', usage='%(prog)s [options]',description='Script to receive changes in directory to a multicast group.')
parser.add_argument('-g','--group', required = True, dest='group_name',type=str, help='Group to connect in')
parser.add_argument('-n','--name', required = True, dest='username',type=str, help='User name')
parser.add_argument('-i','--interface', required = False, default = None, dest='interface',type=str, help='Interface to use')
parser.add_argument('-d','--directory', required = True, dest='directory',type=str, help='Directory to share')

args = parser.parse_args()
serv = server(group_name = args.group_name, username = args.username, interface =args.interface, dirc =  args.directory)
serv.run()
