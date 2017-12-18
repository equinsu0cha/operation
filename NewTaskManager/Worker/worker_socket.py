# coding=utf-8

import SocketServer
import json
import socket
from threading import Thread

from enum import Enum

from NewTaskManager.Controller import controller_logger as logging


class MessageType(Enum):
    CONNECT = 101
    HEARTBEAT = 102
    DISCONNECT = 103


socket_dict = dict()


class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):

    def process(self, data):
        if data.get('MessageType') == MessageType.CONNECT.value:
            socket_dict.update({data.get('SocketID'): self.request})
            return 0
        if data.get('MessageType') == MessageType.HEARTBEAT.value:
            pass
        if data.get('MessageType') == MessageType.DISCONNECT.value:
            logging.info('[socket] disconnect: {0}'.format(self.client_address))
            socket_dict.pop(data.get('SocketID'))
            self.request.close()
            return -1

    def handle(self):
        while True:
            data = self.request.recv(8192)
            if data:
                try:
                    data = json.loads(data)
                    logging.info('[socket] receive: {0}'.format(data))
                except TypeError, e:
                    logging.warning('[socket] format error: {0}'.format(data))
                else:
                    ret = self.process(data)
                    if ret == -1:
                        break
            else:
                logging.warning('[socket] disconnect: {0}'.format(self.client_address))
                break


class WorkerSocketServer(Thread):

    def __init__(self, host, port):
        class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
            pass

        Thread.__init__(self)

        self.socket_server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler)

    @staticmethod
    def send(socket_id, data):
        if isinstance(data, dict):
            data = json.dumps(data)
            try:
                socket_dict.get(socket_id).send(data)
            except socket.error, e:
                socket_dict.pop(socket_id)
                logging.info('[socket] disconnect: {0}'.format(socket_id))
        else:
            logging.warning('[socket] format error: {0}'.format(data))

    def run(self):
        self.socket_server.serve_forever()


if __name__ == '__main__':
    p = WorkerSocketServer('127.0.0.1', 7000)
    p.start()