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
    Station Receptionist
    ~~~~~~~~~~~~~~~~~~~~

    A message scanner for new guests who have just come in.
"""

from json import JSONDecodeError
from threading import Thread
from time import sleep

import dimp

from .database import Database
from .session import SessionServer


class Receptionist(Thread):

    def __init__(self):
        super().__init__()
        self.guests = []
        self.database: Database = None
        self.session_server: SessionServer = None
        self.station = None

    def add_guest(self, identifier: dimp.ID):
        self.guests.append(identifier)

    def run(self):
        print('starting receptionist...')
        while self.station.running:
            try:
                guests = self.guests.copy()
                for identifier in guests:
                    # 1. get all sessions of the receiver
                    print('receptionist: checking session for new guest %s' % identifier)
                    sessions = self.session_server.search(identifier=identifier)
                    if sessions is None or len(sessions) == 0:
                        print('receptionist: guest not connect, remove it: %s' % identifier)
                        self.guests.remove(identifier)
                        continue
                    # 2. this guest is connected, scan new messages for it
                    print('receptionist: %s is connected, scanning messages for it' % identifier)
                    messages = self.database.load_messages(identifier)
                    if messages is None or len(messages) == 0:
                        print('receptionist: no message for this guest, remove it: %s' % identifier)
                        self.guests.remove(identifier)
                        continue
                    # 3. send new messages to each session
                    print('receptionist: got %d message(s) for %s' % (len(messages), identifier))
                    for sess in sessions:
                        handler = sess.request_handler
                        for msg in messages:
                            handler.push_message(msg)
            except IOError as error:
                print('receptionist IO error:', error)
            except JSONDecodeError as error:
                print('receptionist decode error:', error)
            except TypeError as error:
                print('receptionist type error:', error)
            except ValueError as error:
                print('receptionist value error:', error)
            finally:
                # sleep 1 second for next loop
                sleep(1.0)
        print('receptionist exit!')
