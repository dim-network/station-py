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
    Message Dispatcher
    ~~~~~~~~~~~~~~~~~~

    A dispatcher to decide which way to deliver message.
"""

from mkm import is_broadcast
from dimp import ID
from dimp import ReliableMessage
from dimp import ContentType

from libs.common import Database, Facebook, Log
from libs.server import ApplePushNotificationService, SessionServer


class Dispatcher:

    def __init__(self):
        super().__init__()
        self.database: Database = None
        self.facebook: Facebook = None
        self.session_server: SessionServer = None
        self.apns: ApplePushNotificationService = None
        self.neighbors: list = []

    def info(self, msg: str):
        Log.info('%s:\t%s' % (self.__class__.__name__, msg))

    def error(self, msg: str):
        Log.error('%s ERROR:\t%s' % (self.__class__.__name__, msg))

    def __transmit(self, msg: ReliableMessage) -> bool:
        # TODO: broadcast to neighbor stations
        self.info('transmitting to neighbors %s - %s' % (self.neighbors, msg))
        return False

    def __broadcast(self, msg: ReliableMessage) -> bool:
        # TODO: split for all users
        self.info('broadcasting message %s' % msg)
        return False

    def __blocked(self, sender: ID, group: ID) -> bool:
        # TODO: support blocked conversation
        self.info('checking block-list for sender: %s, group: %s' % (sender, group))
        return False

    def __muted(self, sender: ID, group: ID) -> bool:
        # TODO: support muted conversation
        self.info('checking mute-list for sender: %s, group: %s' % (sender, group))
        return False

    def deliver(self, msg: ReliableMessage) -> bool:
        sender = self.facebook.identifier(msg.envelope.sender)
        receiver = self.facebook.identifier(msg.envelope.receiver)
        group = self.facebook.identifier(msg.envelope.group)
        # check broadcast message
        if group is None:
            if is_broadcast(identifier=receiver):
                return self.__broadcast(msg=msg)
        elif is_broadcast(identifier=group):
            return self.__broadcast(msg=msg)
        # check block-list
        if self.__blocked(sender=sender, group=group):
            self.info('this sender/group is blocked: %s' % msg)
            return False
        # try for online user
        sessions = self.session_server.search(identifier=receiver)
        if sessions and len(sessions) > 0:
            self.info('%s is online(%d), try to push message: %s' % (receiver, len(sessions), msg.envelope))
            success = 0
            for sess in sessions:
                if sess.valid is False or sess.active is False:
                    self.info('session invalid %s' % sess)
                    continue
                if sess.request_handler.push_message(msg):
                    success = success + 1
                else:
                    self.error('failed to push message via connection (%s, %s)' % sess.client_address)
            if success > 0:
                self.info('message pushed to activated session(%d) of user: %s' % (success, receiver))
                return True
        # store in local cache file
        self.info('%s is offline, store message: %s' % (receiver, msg.envelope))
        self.database.store_message(msg)
        # transmit to neighbor stations
        self.__transmit(msg=msg)
        if self.__muted(sender=sender, group=group):
            self.info('this sender/group is muted: %s' % msg)
            return True
        # push notification
        msg_type = msg.envelope.type
        return self.__push_msg(sender=sender, receiver=receiver, group=group, msg_type=msg_type)

    def __push_msg(self, sender: ID, receiver: ID, group: ID, msg_type: int) -> bool:
        if msg_type == 0:
            something = 'a message'
        elif msg_type == ContentType.Text:
            something = 'a text message'
        elif msg_type == ContentType.File:
            something = 'a file'
        elif msg_type == ContentType.Image:
            something = 'an image'
        elif msg_type == ContentType.Audio:
            something = 'a voice message'
        elif msg_type == ContentType.Video:
            something = 'a video'
        else:
            self.info('ignore msg type: %s' % msg_type)
            return False
        from_name = self.facebook.nickname(identifier=sender)
        to_name = self.facebook.nickname(identifier=receiver)
        text = 'Dear %s: %s sent you %s' % (to_name, from_name, something)
        # check group
        if group is not None:
            # group message
            gid = self.facebook.identifier(group)
            grp = self.facebook.group(identifier=gid)
            if grp is None:
                g_name = gid.name
            else:
                g_name = grp.name
            text += ' in group [%s]' % g_name
        # push it
        self.info('APNs message: %s' % text)
        return self.apns.push(identifier=receiver, message=text)
