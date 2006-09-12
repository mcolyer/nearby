#!/usr/bin/env python
"""
Nearby - A general message passing framework.
Copyright (C) 2005 Matthew Colyer <linuxcoder@colyer.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from twisted.internet import gtk2reactor
gtk2reactor.install()

import gtk
import pango
from SimpleGladeApp import SimpleGladeApp

from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

import re

class NearbyChat(SimpleGladeApp, LineReceiver):
    def __init__(self, *args):
        self.buffer = gtk.TextBuffer()
        #Highlighted username tag
        self.buffer.create_tag("user", weight=pango.WEIGHT_BOLD, foreground="blue")
	
        SimpleGladeApp.__init__(self, "chat.glade")
        self.received_text.set_buffer(self.buffer)
    
    def connectionMade(self):
        self.sendLine("REGISTER chat 0.1")

    def lineReceived(self, line):
        print "DEBUG:", line
        receiveRe = re.compile("^RECEIVE (\S+) (\S+) (.*)$")
        if not receiveRe.match(line):
            #If we are passed a garbage message fail silently
            return
        nodeid, username, message = receiveRe.match(line).groups(1)
        self.buffer.insert_with_tags_by_name(self.buffer.get_end_iter(), "%s: " % username, "user")
        self.buffer.insert_at_cursor("%s\n" % message)

    def new(self):
	    pass

    def on_file_save(self, widget, data=None):
        pass

    def on_file_open(self, widget, data=None):
        filter = gtk.FileFilter()
        filter.add_pattern("*.txt")
        self.dialog_file_open.set_filter(filter)
        self.dialog_file_open.show()

    def on_file_open_response(self, widget, response, data=None):
        self.dialog_file_open.hide()
        if (response == gtk.RESPONSE_OK):
            pass
    def on_text_entry_key_release(self, widget, event):
        if gtk.gdk.keyval_name(event.keyval) == "Return":
            print "SEND "+self.text_entry.get_text()
            self.sendLine("SEND "+self.text_entry.get_text())

    def on_quit(self, widget):
        self.transport.loseConnection()

class NearbyClientFactory(ClientFactory):
    protocol = NearbyChat

    def startedConnecting(self, connector):
        print "connecting"

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:', reason.getErrorMessage()
        reactor.stop()

def main():
	factory = NearbyClientFactory()
	reactor.connectTCP('localhost', 8002, factory)
	reactor.run()

if __name__ == "__main__":
	main()

#vim: set ts=4 sw=4 expandtab :
