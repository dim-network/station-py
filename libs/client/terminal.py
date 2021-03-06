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
    Terminal
    ~~~~~~~~

    Local User
"""
from typing import Optional

from dimp import ID, EVERYONE, User
from dimp import Content, Command, HandshakeCommand
from dimsdk import Station, Session

from ..common import Facebook

from .connection import Connection
from .cpu import HandshakeDelegate

from .messenger import ClientMessenger


class Terminal(HandshakeDelegate):

    def __init__(self):
        super().__init__()
        self.__messenger: ClientMessenger = None
        # station connection
        self.station: Station = None
        self.session: str = None
        self.connection: Connection = None

    def __del__(self):
        self.disconnect()

    def info(self, msg: str):
        print('\r##### %s > %s' % (self.facebook.current_user.name, msg))

    def error(self, msg: str):
        print('\r!!!!! %s > %s' % (self.facebook.current_user.name, msg))

    def disconnect(self) -> bool:
        if self.connection:
            # if self.messenger.delegate == self.connection:
            #     self.messenger.delegate = None
            self.connection.disconnect()
            self.connection = None
            return True

    def connect(self, station: Station) -> bool:
        conn = Connection()
        conn.connect(station=station)
        mess = self.messenger
        mess.set_context('station', station)
        # delegate for processing received data package
        conn.delegate = mess
        # delegate for sending out data package
        if mess.delegate is None:
            mess.delegate = conn
        self.connection = conn
        self.station = station
        return True

    @property
    def messenger(self) -> ClientMessenger:
        return self.__messenger

    @messenger.setter
    def messenger(self, value: ClientMessenger):
        self.__messenger = value

    @property
    def facebook(self) -> Facebook:
        return self.messenger.facebook

    def send_command(self, cmd: Command) -> bool:
        """ Send command to current station """
        return self.messenger.send_content(content=cmd, receiver=self.station.identifier)

    def broadcast_content(self, content: Content, receiver: ID) -> bool:
        content.group = EVERYONE
        return self.messenger.send_content(content=content, receiver=receiver)

    def handshake(self):
        cmd = HandshakeCommand.start()
        return self.send_command(cmd=cmd)

    #
    #   HandshakeDelegate
    #
    def handshake_accepted(self, session: Session) -> Optional[Content]:
        self.info('handshake accepted: %s' % session)
        return None

    def handshake_success(self) -> Optional[Content]:
        self.info('handshake success')
        return None
