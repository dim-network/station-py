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
    Message Processor
    ~~~~~~~~~~~~~~~~~

    Message processor for Request Handler
"""

import dimp

from .session import Session
from .config import station, session_server, database, dispatcher, receptionist, monitor


class MessageProcessor:

    def __init__(self, request_handler):
        super().__init__()
        self.request_handler = request_handler
        self.station = station
        self.session_server = session_server
        self.database = database
        self.dispatcher = dispatcher
        self.receptionist = receptionist

    @property
    def client_address(self) -> str:
        return self.request_handler.client_address

    @property
    def identifier(self) -> dimp.ID:
        return self.request_handler.identifier

    def current_session(self, identifier: dimp.ID=None) -> Session:
        return self.request_handler.current_session(identifier=identifier)

    """
        main entrance
    """
    def process(self, msg: dimp.ReliableMessage) -> dimp.Content:
        # verify signature
        s_msg = self.station.verify_message(msg)
        if s_msg is None:
            print('MessageProcessor: message verify error', msg)
            response = dimp.TextContent.new(text='Signature error')
            response['signature'] = msg.signature
            return response
        # check receiver & session
        sender = dimp.ID(s_msg.envelope.sender)
        receiver = dimp.ID(s_msg.envelope.receiver)
        if receiver == self.station.identifier:
            # the client is talking with station (handshake, search users, get meta/profile, ...)
            content = self.station.decrypt_message(s_msg)
            if content.type == dimp.MessageType.Command:
                print('MessageProcessor: command from client', self.client_address, content)
                return self.process_command(sender=sender, content=content)
            # talk with station?
            print('MessageProcessor: message from client', self.client_address, content)
            return self.process_dialog(sender=sender, content=content)
        # check session valid
        session = self.current_session(identifier=sender)
        if not session.valid:
            # session invalid, handshake first
            # NOTICE: if the client try to send message to another user before handshake,
            #         the message will be lost!
            return self.process_handshake(sender)
        # deliver message for receiver
        print('MessageProcessor: delivering message', msg.envelope)
        return self.deliver_message(msg)

    def process_dialog(self, sender: dimp.ID, content: dimp.Content) -> dimp.Content:
        print('@@@ call NLP and response to the client', self.client_address, sender)
        # TEST: response client with the same message here
        return content

    def process_command(self, sender: dimp.ID, content: dimp.Content) -> dimp.Content:
        command = content['command']
        if 'handshake' == command:
            # handshake protocol
            return self.process_handshake(sender=sender, cmd=dimp.HandshakeCommand(content))
        elif 'meta' == command:
            # meta protocol
            return self.process_meta_command(cmd=dimp.MetaCommand(content))
        elif 'profile' == command:
            # profile protocol
            return self.process_profile_command(cmd=dimp.ProfileCommand(content))
        elif 'users' == command:
            # show online users (connected)
            return self.process_users_command()
        elif 'search' == command:
            # search users with keyword(s)
            return self.process_search_command(cmd=dimp.CommandContent(content))
        elif 'broadcast' == command:
            session = self.current_session(identifier=sender)
            if not session.valid:
                # session invalid, handshake first
                return self.process_handshake(sender)
            # broadcast
            return self.process_broadcast_command(cmd=dimp.BroadcastCommand(content))
        else:
            print('MessageProcessor: unknown command', content)

    def process_handshake(self, sender: dimp.ID, cmd: dimp.HandshakeCommand=None) -> dimp.Content:
        # set/update session in session server with new session key
        print('MessageProcessor: handshake with client', self.client_address, sender)
        if cmd is None:
            session_key = None
        else:
            session_key = cmd.session
        session = self.current_session(identifier=sender)
        if session_key == session.session_key:
            # session verified success
            session.valid = True
            session.active = True
            print('MessageProcessor: handshake accepted', self.client_address, sender, session_key)
            monitor.report(message='User logged in %s %s' % (self.client_address, sender))
            # add the new guest for checking offline messages
            self.receptionist.add_guest(identifier=sender)
            return dimp.HandshakeCommand.success()
        else:
            # session key not match, ask client to sign it with the new session key
            return dimp.HandshakeCommand.again(session=session.session_key)

    def process_meta_command(self, cmd: dimp.MetaCommand) -> dimp.Content:
        identifier = cmd.identifier
        meta = cmd.meta
        if meta:
            # received a meta for ID
            meta = dimp.Meta(meta)
            print('MessageProcessor: received meta', identifier)
            if self.database.save_meta(identifier=identifier, meta=meta):
                # meta saved
                return dimp.ReceiptCommand.receipt(message='Meta for %s received!' % identifier)
            else:
                # meta not match
                return dimp.TextContent.new(text='Meta not match %s!' % identifier)
        else:
            # querying meta for ID
            print('MessageProcessor: search meta', identifier)
            meta = self.database.meta(identifier=identifier)
            if meta:
                return dimp.MetaCommand.response(identifier=identifier, meta=meta)
            else:
                return dimp.TextContent.new(text='Sorry, meta for %s not found.' % identifier)

    def process_profile_command(self, cmd: dimp.ProfileCommand) -> dimp.Content:
        identifier = cmd.identifier
        meta = cmd.meta
        if meta is not None:
            if self.database.save_meta(identifier=identifier, meta=meta):
                # meta saved
                print('MessageProcessor: meta cached', identifier, meta)
            else:
                print('MessageProcessor: meta not match', identifier, meta)
        profile = cmd.profile
        if profile is not None:
            # received a new profile for ID
            print('MessageProcessor: received profile', identifier)
            if self.database.save_profile(profile=profile):
                # profile saved
                return dimp.ReceiptCommand.receipt(message='Profile of %s received!' % identifier)
            else:
                # signature not match
                return dimp.TextContent.new(text='Profile signature not match %s!' % identifier)
        else:
            # querying profile for ID
            print('MessageProcessor: search profile', identifier)
            profile = self.database.profile(identifier=identifier)
            if profile is not None:
                return dimp.ProfileCommand.response(identifier=identifier, profile=profile)
            else:
                return dimp.TextContent.new(text='Sorry, profile for %s not found.' % identifier)

    def process_users_command(self) -> dimp.Content:
        print('MessageProcessor: get online user(s) for', self.identifier)
        users = self.session_server.random_users(max_count=20)
        response = dimp.CommandContent.new(command='users')
        response['message'] = '%d user(s) connected' % len(users)
        response['users'] = users
        return response

    def process_search_command(self, cmd: dimp.CommandContent) -> dimp.Content:
        print('MessageProcessor: search users for', self.identifier, cmd)
        # keywords
        keywords = cmd.get('keywords')
        if keywords is None:
            keywords = cmd.get('keyword')
            if keywords is None:
                keywords = cmd.get('kw')
        # search for each keyword
        if keywords is None:
            keywords = []
        else:
            keywords = keywords.split(' ')
        results = self.database.search(keywords=keywords)
        # response
        users = list(results.keys())
        response = dimp.CommandContent.new(command='search')
        response['message'] = '%d user(s) found' % len(users)
        response['users'] = users
        response['results'] = results
        return response

    def process_broadcast_command(self, cmd: dimp.BroadcastCommand) -> dimp.Content:
        print('MessageProcessor: client broadcast', self.identifier, cmd)
        title = cmd.title
        if 'report' == title:
            # report client state
            state = cmd.get('state')
            print('MessageProcessor: client report state', state)
            if state is not None:
                session = self.current_session()
                if 'background' == state:
                    session.active = False
                elif 'foreground' == state:
                    # welcome back!
                    receptionist.add_guest(identifier=session.identifier)
                    session.active = True
                else:
                    print('MessageProcessor: unknown state', state)
                    session.active = True
                return dimp.ReceiptCommand.receipt(message='Client state received')
        elif 'apns' == title:
            # submit device token for APNs
            token = cmd.get('device_token')
            print('MessageProcessor: client report token', token)
            if token is not None:
                self.database.save_device_token(identifier=self.identifier, token=token)
                return dimp.ReceiptCommand.receipt(message='Token received')
        else:
            print('MessageProcessor: unknown broadcast command', cmd)

    def deliver_message(self, msg: dimp.ReliableMessage) -> dimp.Content:
        print('MessageProcessor: deliver message', self.identifier, msg.envelope)
        self.dispatcher.deliver(msg)
        # response to sender
        response = dimp.ReceiptCommand.receipt(message='Message delivering')
        # extra info
        sender = msg.get('sender')
        receiver = msg.get('receiver')
        time = msg.get('time')
        group = msg.get('group')
        signature = msg.get('signature')
        # envelope
        response['sender'] = sender
        response['receiver'] = receiver
        if time is not None:
            response['time'] = time
        # group message?
        if group is not None and group != receiver:
            response['group'] = group
        # signature
        response['signature'] = signature
        return response
