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

import os
import time

import dimp

from .utils import json_dict, json_str, base64_decode


class Database(dimp.Barrack, dimp.KeyStore):

    def __init__(self):
        super().__init__()
        self.base_dir = '/tmp/.dim/'

    def directory(self, control: str, identifier: dimp.ID, sub_dir: str='') -> str:
        path = self.base_dir + control + '/' + identifier.address
        if sub_dir:
            path = path + '/' + sub_dir
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    """
        Reliable message for Receivers
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        file path: '.dim/public/{ADDRESS}/messages/*.msg'
    """

    def store_message(self, msg: dimp.ReliableMessage) -> bool:
        receiver = dimp.ID(msg.envelope.receiver)
        directory = self.directory('public', receiver, 'messages')
        filename = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        path = directory + '/' + filename + '.msg'
        with open(path, 'a') as file:
            file.write(json_str(msg) + '\n')
        print('msg write into file: ', path)
        return True

    def load_messages(self, receiver: dimp.ID) -> list:
        directory = self.directory('public', receiver, 'messages')
        # get all files in messages directory and sort by filename
        files = sorted(os.listdir(directory))
        for filename in files:
            if filename[-4:] == '.msg':
                path = directory + '/' + filename
                # read ONE .msg file for each receiver and remove the file immediately
                with open(path, 'r') as file:
                    data = file.read()
                os.remove(path)
                print('read %d byte(s) from %s' % (len(data), path))
                # ONE line ONE message, split them
                lines = str(data).splitlines()
                messages = [dimp.ReliableMessage(json_dict(line)) for line in lines]
                print('got %d message(s) for %s' % (len(messages), receiver))
                return messages

    """
        Meta file for Accounts
        ~~~~~~~~~~~~~~~~~~~~~~

        file path: '.dim/public/{ADDRESS}/meta.js'
    """

    def save_meta(self, meta: dimp.Meta, identifier: dimp.ID) -> bool:
        if not meta.match_identifier(identifier):
            print('meta not match %s: %s, IGNORE!' % (identifier, meta))
            return False
        # save meta as new file
        directory = self.directory('public', identifier)
        path = directory + '/meta.js'
        if os.path.exists(path):
            print('meta file exists: %s, update IGNORE!' % path)
        else:
            with open(path, 'w') as file:
                file.write(json_str(meta))
            print('meta write into file: ', path)
        # update memory cache
        return super().retain_meta(meta=meta, identifier=identifier)

    def meta(self, identifier: dimp.ID) -> dimp.Meta:
        meta = super().meta(identifier=identifier)
        if meta is not None:
            return meta
        # load from local storage
        directory = self.directory('public', identifier)
        path = directory + '/meta.js'
        if os.path.exists(path):
            with open(path, 'r') as file:
                data = file.read()
                # no need to check meta again
                return dimp.Meta(json_dict(data))

    """
        Profile for Accounts
        ~~~~~~~~~~~~~~~~~~~~

        file path: '.dim/public/{ADDRESS}/profile.js'
    """

    def save_profile_signature(self, identifier: dimp.ID, profile: str, signature: str) -> bool:
        meta = self.meta(identifier=identifier)
        if meta:
            pk = meta.key
            data = profile.encode('utf-8')
            sig = base64_decode(signature)
            if not pk.verify(data, sig):
                print('signature not match %s: %s, %s' % (identifier, profile, signature))
                return False
        else:
            print('meta not found: %s, IGNORE!' % identifier)
            return False
        # save/update profile
        content = {
            'ID': identifier,
            'profile': profile,
            'signature': signature,
        }
        directory = self.directory('public', identifier)
        path = directory + '/profile.js'
        with open(path, 'w') as file:
            file.write(json_str(content))
        print('profile write into file: ', path)
        # update memory cache
        return self.retain_profile(profile=json_dict(profile), identifier=identifier)

    def profile(self, identifier: dimp.ID) -> dict:
        profile = super().profile(identifier=identifier)
        if profile is not None:
            return profile
        # load from local storage
        directory = self.directory('public', identifier)
        path = directory + '/profile.js'
        if os.path.exists(path):
            with open(path, 'r') as file:
                data = file.read()
                # no need to check signature again
                return json_dict(data)

    """
        Private Key file for Users
        ~~~~~~~~~~~~~~~~~~~~~~~~~~

        file path: '.dim/private/{ADDRESS}/private_key.js'
    """

    def save_private_key(self, private_key: dimp.PrivateKey, identifier: dimp.ID) -> bool:
        meta = self.meta(identifier=identifier)
        if meta is None:
            print('meta not found: %s' % identifier)
            return False
        elif not meta.key.match(private_key=private_key):
            print('private key not match %s: %s' % (identifier, private_key))
            return False
        # save private key as new file
        directory = self.directory('private', identifier)
        path = directory + '/private_key.js'
        if os.path.exists(path):
            print('private key file exists: %s, update IGNORE!' % path)
        else:
            with open(path, 'w') as file:
                file.write(json_str(private_key))
            print('private key write into file: ', path)
        # update memory cache
        super().retain_private_key(private_key=private_key, identifier=identifier)
        return True

    def private_key(self, identifier: dimp.ID) -> dimp.PrivateKey:
        sk = super().private_key(identifier=identifier)
        if sk is not None:
            return sk
        # load from local storage
        directory = self.directory('private', identifier)
        path = directory + '/private_key.js'
        if os.path.exists(path):
            with open(path, 'r') as file:
                data = file.read()
                return dimp.PrivateKey(json_dict(data))

    """
        Key Store
        ~~~~~~~~~
        
        Memory cache for reused passwords (symmetric key)
    """

    def cipher_key(self, sender: str = None, receiver: str = None, group: str = None) -> dict:
        key = super().cipher_key(sender=sender, receiver=receiver, group=group)
        if key is not None:
            return key
        key = dimp.SymmetricKey.generate({'algorithm': 'AES'})
        self.retain_cipher_key(key=key, sender=sender, receiver=receiver, group=group)
        return key

    """
        Search Engine
        ~~~~~~~~~~~~~
        
        Search accounts by the 'Search Number'
    """

    def search(self, keyword: str, accounts: dict=None) -> dict:
        if accounts is None:
            accounts = self.accounts
        results = {}
        for identifier in accounts:
            identifier = dimp.ID(identifier)
            network = identifier.address.network
            if not network.is_person() and not network.is_group():
                # ignore
                continue
            if identifier.find(keyword) < 0 and str(identifier.number).find(keyword) < 0:
                # not match
                continue
            # got it
            meta = self.meta(identifier)
            if meta:
                results[identifier] = meta
        return results
