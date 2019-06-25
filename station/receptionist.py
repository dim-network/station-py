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

from dimp import ID

from common import database, Log
from common import s001

from .session import session_server
from .apns import apns


class Receptionist(Thread):

    def __init__(self):
        super().__init__()
        self.guests = []
        self.apns = None

    def add_guest(self, identifier: ID):
        self.guests.append(identifier)

    def run(self):
        Log.info('Receptionist: starting...')
        while station.running:
            try:
                guests = self.guests.copy()
                for identifier in guests:
                    # 1. get all sessions of the receiver
                    Log.info('Receptionist: checking session for new guest %s' % identifier)
                    sessions = session_server.search(identifier=identifier)
                    if sessions is None or len(sessions) == 0:
                        Log.info('Receptionist: guest not connect, remove it: %s' % identifier)
                        self.guests.remove(identifier)
                        continue
                    # 2. this guest is connected, scan new messages for it
                    Log.info('Receptionist: %s is connected, scanning messages for it' % identifier)
                    batch = database.load_message_batch(identifier)
                    if batch is None:
                        Log.info('Receptionist: no message for this guest, remove it: %s' % identifier)
                        self.guests.remove(identifier)
                        self.apns.clear_badge(identifier=identifier)
                        continue
                    messages = batch.get('messages')
                    if messages is None or len(messages) == 0:
                        Log.info('Receptionist: message batch error: %s' % batch)
                        # raise AssertionError('message batch error: %s' % batch)
                        continue
                    # 3. send new messages to each session
                    Log.info('Receptionist: got %d message(s) for %s' % (len(messages), identifier))
                    count = 0
                    for msg in messages:
                        # try to push message
                        success = 0
                        for sess in sessions:
                            if sess.valid is False or sess.active is False:
                                Log.info('Receptionist: session invalid %s' % sess)
                                continue
                            if sess.request_handler.push_message(msg):
                                success = success + 1
                            else:
                                Log.info('Receptionist: failed to push message (%s, %s)' % sess.client_address)
                        if success > 0:
                            # push message success (at least one)
                            count = count + 1
                        else:
                            # push message failed, remove session here?
                            break
                    # 4. remove messages after success, or remove the guest on failed
                    total_count = len(messages)
                    Log.info('Receptionist: a batch message(%d/%d) pushed to %s' % (count, total_count, identifier))
                    database.remove_message_batch(batch, removed_count=count)
                    if count < total_count:
                        Log.info('Receptionist: pushing message failed, remove the guest: %s' % identifier)
                        self.guests.remove(identifier)
            except IOError as error:
                Log.info('Receptionist: IO error %s' % error)
            except JSONDecodeError as error:
                Log.info('Receptionist: decode error %s' % error)
            except TypeError as error:
                Log.info('Receptionist: type error %s' % error)
            except ValueError as error:
                Log.info('Receptionist: value error %s' % error)
            finally:
                # sleep 1 second for next loop
                sleep(1.0)
        Log.info('Receptionist: exit!')


receptionist = Receptionist()
receptionist.database = database
receptionist.session_server = session_server
receptionist.apns = apns


"""
    Current Station
    ~~~~~~~~~~~~~~~
"""
station = s001
