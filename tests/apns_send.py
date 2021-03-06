#! /usr/bin/env python3
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
    Send SMS
    ~~~~~~~~

    Usage:
        ./send.py moky@4DnqXWdTV8wuZgfqSCX9GjE2kNq7HJrUgQ "Hello!"
"""

import json
import os
import sys

from apns2.client import APNsClient
from apns2.payload import Payload

from dimp import ID


"""
    Configuration
"""
base_dir = '/data/.dim/'

credentials = '/srv/dims/etc/apns/credentials.pem'
use_sandbox = True


class Device:
    """ Get device tokens """

    def __init__(self, identifier: str):
        self.__identifier = ID(identifier)

    @property
    def path(self) -> str:
        address = self.__identifier.address
        return base_dir + '/protected/' + address + '/device.js'

    @property
    def tokens(self) -> list:
        path = self.path
        if os.path.exists(path):
            with open(path, 'r') as file:
                data = file.read()
            device = json.loads(data)
            # TODO: only get the last two devices
            return device.get('tokens')


class SMS:
    """ Push SMS via APNs """

    def __init__(self, text: str):
        self.__client = APNsClient(credentials=credentials, use_sandbox=use_sandbox)
        self.__payload = Payload(alert=text)

    def send(self, identifier: str) -> int:
        identifier = ID(identifier)
        device = Device(identifier)
        tokens = device.tokens
        if tokens is None:
            print('Device token not found, failed to push message: %s' % self.__payload.alert)
            return 0
        count = 0
        for token in tokens:
            self.__client.send_notification(token_hex=token, notification=self.__payload)
            count += 1
        print('Message has been sent to %d device(s)' % count)
        return count


def send(text: str, identifier: str) -> bool:
    msg = SMS(text=text)
    count = msg.send(identifier=identifier)
    return count > 0


if __name__ == '__main__':
    # check arguments
    if len(sys.argv) == 3:
        send(text=sys.argv[2], identifier=sys.argv[1])
    else:
        print('Usage:')
        print('    %s "ID" "text"' % sys.argv[0])
        print('')
