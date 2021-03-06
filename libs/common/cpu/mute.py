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
    Command Processor for 'mute'
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Mute protocol
"""

from dimp import ID
from dimp import InstantMessage
from dimp import Content, TextContent
from dimp import Command
from dimsdk import ReceiptCommand, MuteCommand
from dimsdk import CommandProcessor

from ..database import Database


class MuteCommandProcessor(CommandProcessor):

    @property
    def database(self) -> Database:
        return self.get_context('database')

    def __get(self, sender: ID) -> Content:
        stored: Command = self.database.mute_command(identifier=sender)
        if stored is not None:
            # response the stored mute command directly
            return stored
        else:
            # return TextContent.new(text='Sorry, mute-list of %s not found.' % sender)
            # TODO: here should response an empty HistoryCommand: 'mute'
            res = Command.new(command='mute')
            res['list'] = []
            return res

    def __put(self, cmd: MuteCommand, sender: ID) -> Content:
        # receive mute command, save it
        if self.database.save_mute_command(cmd=cmd, sender=sender):
            return ReceiptCommand.new(message='Mute command of %s received!' % sender)
        else:
            return TextContent.new(text='Sorry, mute-list not stored %s!' % cmd)

    #
    #   main
    #
    def process(self, content: Content, sender: ID, msg: InstantMessage) -> Content:
        assert isinstance(content, MuteCommand), 'command error: %s' % content
        if 'list' in content:
            # upload mute-list, save it
            return self.__put(cmd=content, sender=sender)
        else:
            # query mute-list, load it
            return self.__get(sender=sender)


# register
CommandProcessor.register(command='mute', processor_class=MuteCommandProcessor)
