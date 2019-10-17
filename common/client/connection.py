# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

"""
    Socket Connection
    ~~~~~~~~~~~~~~~~~

    Connection for DIM Station and Robot Client
"""

import socket
from abc import ABCMeta, abstractmethod
from threading import Thread

from dimp import Station, ITransceiverDelegate, ICompletionHandler
from dkd import InstantMessage


class IConnectionDelegate(metaclass=ABCMeta):

    @abstractmethod
    def receive_package(self, data: bytes):
        """ Receive data package

        :param data: data package
        :return:
        """
        pass


class Connection(ITransceiverDelegate):

    # boundary for packages
    BOUNDARY = b'\n'

    def __init__(self):
        super().__init__()
        # socket
        self.sock = None
        self.thread_receive = None
        self.connected = False
        self.delegate: IConnectionDelegate = None

    def __del__(self):
        self.close()

    def close(self):
        # stop thread
        self.connected = False
        if self.thread_receive:
            self.thread_receive = None
        # disconnect the socket
        if self.sock:
            self.sock.close()

    def connect(self, station: Station):
        if self.sock:
            self.sock.close()
        # connect to new socket (host:port)
        address = (station.host, station.port)
        self.sock = socket.socket()
        self.sock.connect(address)
        # start threads
        self.connected = True
        if self.thread_receive is None:
            self.thread_receive = Thread(target=receive_handler, args=(self,))
            self.thread_receive.start()

    def receive(self, pack: bytes):
        self.delegate.receive_package(data=pack)

    #
    #   ITransceiverDelegate
    #
    def send_package(self, data: bytes, handler: ICompletionHandler) -> bool:
        """ Send out a data package onto network """
        # pack
        pack = data + self.BOUNDARY
        # send
        self.sock.sendall(pack)
        if handler is not None:
            handler.success()
        return True

    def upload_data(self, data: bytes, msg: InstantMessage) -> str:
        """ Upload encrypted data to CDN """
        pass

    def download_data(self, url: str, msg: InstantMessage) -> bytes:
        """ Download encrypted data from CDN, and decrypt it when finished """
        pass


def receive_handler(conn: Connection):
    data = b''
    while conn.connected:
        # read all data
        try:
            data += conn.sock.recv(1024)
        except OSError:
            break
        # split package(s)
        pos = data.find(conn.BOUNDARY)
        while pos != -1:
            pack = data[:pos]
            conn.receive(pack=pack)
            # next package
            pos += len(conn.BOUNDARY)
            data = data[pos:]
            pos = data.find(conn.BOUNDARY)
