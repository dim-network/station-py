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
    Facebook
    ~~~~~~~~

    Barrack for cache entities
"""

from typing import Optional

from dimp import PrivateKey
from dimp import ID, Meta, Profile
from dimsdk import Facebook as Barrack

from .database import Database


class Facebook(Barrack):

    def __init__(self):
        super().__init__()
        self.database: Database = None

    def nickname(self, identifier: ID) -> str:
        assert identifier.type.is_user(), 'ID error: %s' % identifier
        user = self.user(identifier=identifier)
        if user is not None:
            return user.name

    def group_name(self, identifier: ID) -> str:
        assert identifier.type.is_group(), 'ID error: %s' % identifier
        group = self.group(identifier=identifier)
        if group is None:
            return identifier.name
        else:
            return group.name

    #
    #   super()
    #
    def save_meta(self, meta: Meta, identifier: ID) -> bool:
        if not self.cache_meta(meta=meta, identifier=identifier):
            return False
        return self.database.save_meta(meta=meta, identifier=identifier)

    def load_meta(self, identifier: ID) -> Optional[Meta]:
        return self.database.meta(identifier=identifier)

    def save_profile(self, profile: Profile, identifier: ID=None) -> bool:
        if not self.cache_profile(profile=profile, identifier=identifier):
            # profile error
            return False
        return self.database.save_profile(profile=profile)

    def load_profile(self, identifier: ID) -> Optional[Profile]:
        return self.database.profile(identifier=identifier)

    def save_private_key(self, private_key: PrivateKey, identifier: ID) -> bool:
        return self.database.save_private_key(private_key=private_key, identifier=identifier)

    def load_private_key(self, identifier: ID) -> Optional[PrivateKey]:
        return self.database.private_key(identifier=identifier)

    def save_contacts(self, contacts: list, identifier: ID) -> bool:
        return self.database.save_contacts(contacts=contacts, user=identifier)

    def load_contacts(self, identifier: ID) -> Optional[list]:
        return self.database.contacts(user=identifier)

    def save_members(self, members: list, identifier: ID) -> bool:
        return self.database.save_members(members=members, group=identifier)

    def load_members(self, identifier: ID) -> Optional[list]:
        return self.database.members(group=identifier)

    #
    #    IGroupDataSource
    #
    def founder(self, identifier: ID) -> ID:
        # get from database
        user = self.database.founder(group=identifier)
        if user is not None:
            return user
        return super().founder(identifier=identifier)

    def owner(self, identifier: ID) -> ID:
        # get from database
        user = self.database.owner(group=identifier)
        if user is not None:
            return user
        return super().owner(identifier=identifier)
