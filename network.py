#   JTM 2021
#   custom network communications class v2.0

import socket
import sys, time
from _thread import *
import threading
from timer import Timer

class Network_Sock:
    #function initializes socket object and variables
    def __init__(self, message_size=256, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

        self.message_size = message_size
        self.master = False
        self.clientsock = None
        self.clientaddr = None

        self.queue_in = []
        self.sthread = None

        self.th_flag = False
    
    #bind function to host a socket on the designated host and port
    #host defaults to local IP address if no arg given
    def bind(self, port, host=None):
        if host is None:
            host = self.sock.gethostbyname(self.sock.gethostname())
        #bind the socket and start 5 listeners
        self.sock.bind((host, port))
        self.sock.listen(5)
        #designate that this object is the master
        self.master = True

    #connect to a socket on another computer
    #takes a host ip and a port number
    def connect(self, host, port):
        #connect to the socket
        try:
            self.sock.connect((host, port))
            self.sock.settimeout(.1)
            return True
        except:
            return False


    def is_connected(self):
        if self.sock is None:
            return False
        else:
            return True


    #send a message to the connected device
    #message should be an encoded string, encoding and handling of data not performed
    def send(self, msg):
        #if this is the master object, send a message using the client socket connection
        #if no connection exists, accept it now and send the message
        if self.master:
            if self.clientsock is None:
                self.clientsock, self.clientaddr = self.sock.accept()
            self.clientsock.send(msg)
        #otherwise send the message using the socket object
        else:
            self.sock.send(msg)


    #receive data from the connected socket
    #message will be an encoded string, decodeing and handling of data not performed
    def receive(self):
        #if this is the master object, the client socket connection should be used to 
        #receive message_size chars
        try:
            if self.master:
                msg = self.clientsock.recv(self.message_size)
            #otherwise receive data with the socket object
            else:
                msg = self.sock.recv(self.message_size)
            #if the message has contents, return it
            if msg:
                #print(f'message receive: {msg}')
                return msg
            else:
                return None
        except socket.timeout:
            return None


    def receive_thread(self, timeout=1.0):
        th_timer = Timer(timeout)
        #th_timer.start()
        while self.th_flag: #and not th_timer.expired()
            mes = self.receive()
            if mes:
                self.queue_in.append(mes.decode())
            time.sleep(.0001)


    def start_receive_thread(self):
        if self.sock is not None:
            self.th_flag = True
            self.sthread = threading.Thread(target=self.receive_thread)
            self.sthread.daemon = True
            self.sthread.start()


    #function to close all connections
    def close(self):
        #if this is the master object, close the clientsock connection
        #make it a none type and reset address/master var
        if self.master:
            self.clientsock.close()
            self.clientsock = None 
            self.address = None 
            self.master = False
        #otherwise close the current socket connection
        else:
            self.sock.close()

    def pop_from_queue(self):
        return self.queue_in[0]

    def pop_latest_from_queue(self):
        return self.queue_in[-1]

    def reset_queue(self):
        self.queue_in = []