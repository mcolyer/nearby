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

import Zeroconf
import socket
import logging

log = logging.getLogger("nearby")

server = Zeroconf.Zeroconf()
service = None

class NewHostListener(object):
    """The zeroconf listener which looks for new nodes and the removal of old
    nodes on the network."""
    
    def removeService(self, server, type, name):
        log.debug("Service %s removed" % repr(name))

    def addService(self, server, type, name):
        log.debug("Service %s added" % repr(name))
        
        # Request more information about the service
        info = server.getServiceInfo(type, name)
        
        log.debug(info.properties)

        # Notify the Twisted thread that there is a new host online
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 8001))
        s.send(repr({"ip" : socket.inet_ntoa(info.getAddress()), "port" : info.getPort(), "subservices" : info.properties["subservices"]}))
        s.close()

def init():
        # Start the zeroconf listener
        listener = NewHostListener()
        browser = Zeroconf.ServiceBrowser(server, "_nearby._tcp.local.", listener)
