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

import signal
import socket
import threading
import re
import Zeroconf
import logging

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor
from twisted.web import static, server
from twisted.spread import pb
from twisted.python import util

import discover

#Determine which operating system we are running in
import platform
try:
    platform.win32_ver()
    import windows as OsSpecific
except:
    import linux as OsSpecific

#Configure the logging mechanisms
logging.basicConfig()
log = logging.getLogger("nearby")
log.setLevel(logging.DEBUG)

# This is where all the outbound nodes are stored. The key is the ip address.
outbound_nodes = {}

# This is where all the local plugin connections are stored. The key is the subservice name.
local_subservices = {}

node_name = OsSpecific.getName()

# Choose a node name and id
node_id = "%s-%s" % (socket.gethostbyname(socket.gethostname()), node_name)

class Nearby(pb.Root):
    """This is the remote object which facilities the communications between
    the local network and the local subservices."""

    def remote_query(self):
        """Returns information about the node."""
        local_ip = socket.gethostbyname(socket.gethostname())

        return (node_name, local_ip)

    def remote_message(self, node_name, node_id, subservice, version, message):
        if local_subservices.has_key(subservice) and local_subservices[subservice]["version"] == version:
            subservice_connection = local_subservices[subservice]["connection"].transport
            log.debug("SEND TO LOCAL RECEIVE %s %s %s" % (node_id, node_name, message))
            subservice_connection.write("RECEIVE %s %s %s\n" % (node_id, node_name, message))

class NearbyClientFactory(pb.PBClientFactory):
    """The object which spawns outbound connections to other nodes on the network."""

    def clientConnectionLost(self, connector, reason, reconnecting = 0):
        #Remove the client from the global list when they disconnect
        del(outbound_nodes[connector.getDestination().host])
        log.debug("Removed: %s" % outbound_nodes)

class NearbyLocal(Protocol):
    """Handles connections from local clients that wish to talk on the
    network."""

    def dataReceived(self, data):
        sendRe = re.compile("^SEND (.*)")
        registerRe = re.compile("^REGISTER (\w+) (\S+).*$")
        
        if sendRe.match(data):
            log.debug("SEND MSG")
            message = sendRe.match(data).groups()[0]
            for remote_ip,data in outbound_nodes.iteritems():
                data["ro"].callRemote("message", node_name, node_id, self.service, self.version, message)
                
        elif registerRe.match(data):
            log.debug("REGISTER MSG")
            log.debug(registerRe.match(data).groups(1))

            self.service, self.version = registerRe.match(data).groups(1)

            #If we already have a plugin connected providing the service, tell
            #the new plugin to unregister and disconnect
            if local_subservices.has_key(self.service):
                log.warn("Local plugin attempted to register an service which is currently running.")
                self.transport.write("UNREGISTER\n")
                return
                
            local_subservices[self.service] = {"version" : self.version, "connection" : self}
            myService.updateSubservices()
        else:
            log.error("Invalid message on the local communication channel.")
            return

    def connectionLost(self, reason):
        #Remove this subservice when it disconnects.
        for subservice,data in local_subservices.iteritems():
            if data["connection"] == self:
                log.debug("Removing subservice: %s" % subservice)
                del(local_subservices[subservice])
                myService.updateSubservices()
                return

class Discovery(Protocol):
    """Connects to new nodes as the appear on the network."""

    def dataReceived(self, data):
        dataRe = re.compile("{'ip': '([0-9\.]+)', 'port': ([0-9]+), 'subservices': (.*?)}")
        result = dataRe.match(data)

        # Check to make sure the data is in the proper format.
        if not result:
            log.error("Invalid message format on the interthread communication channel")
            return

        ip, port, subservices = result.groups(1)
        port = int(port)

        # FIXME: This is poor poor security
        subservices = eval(eval(subservices))
        
        # Create a connection with the new peer if we are not already connected.
        # The only time that this will occur is if subservices are added to another
        # node on the network as it must remove itself and readd itself when
        # updating a list of subservices available.
        if ip not in outbound_nodes.keys():
            factory = NearbyClientFactory()
            reactor.connectTCP(ip, port, factory)
            d = factory.getRootObject()
            d.addCallback(self.neogiate, subservices)
            d.addErrback(self.errorHandler)
        else:
            # The service was added and then removed to update its services.
            outbound_nodes[ip]["subservices"] = subservices
    
    def neogiate(self, ro, subservices):
        """Connects to the remote object and adds it to the list of connected
        remote objects."""

        d = ro.callRemote("query")
        
        def appendToOutboundNodes(result):
            name, ip = result

            outbound_nodes[ip] = {"name" : name, "ro" : ro, "subservices" : subservices}
            log.debug("Added: %s" % outbound_nodes)
            return outbound_nodes
        d.addCallback(appendToOutboundNodes)
        
    def errorHandler(self, error):
        log.error(error)

class NearbyService:
    def advertise(self):
        """Advertises the existence of this node to the network and the services
        its providing.
        """
        local_ip = socket.gethostbyname(socket.gethostname())
        local_ip = socket.inet_aton(local_ip)
        
        # Create a list of tuples representing the subservices and their
        # version which are available from this node
        subservices_and_versions = []
        for name,data in local_subservices.iteritems():
            version = data["version"]
            subservices_and_versions.append((name, version))
        
        discover.service = Zeroconf.ServiceInfo("_nearby._tcp.local.",
                                    socket.inet_ntoa(local_ip)+"._nearby._tcp.local.",
                                    address = local_ip,
                                    port = 8000,
                                    weight = 0, priority=0,
                                    properties = {"description": "A simple peer communication network",
                                                  "subservices" : repr(subservices_and_versions)
                                                 }
                                   )
        discover.server.registerService(discover.service)
        
    def updateSubservices(self):
        """This function is called when another plugin is started locally."""
        discover.server.unregisterService(discover.service)
        self.advertise()

    def start(self):
        # Start the zeroconf subsystem
        discover.init()
        
        # Setup the callback to shutdown
        signal.signal(signal.SIGINT, self.stop)

        # Create the listener
        reactor.listenTCP(8000, pb.PBServerFactory(Nearby()))

        # Listen for new hosts in the twisted thread
        f = Factory()
        f.protocol = Discovery
        reactor.listenTCP(8001, f)

        # Listen for new plugins
        f = Factory()
        f.protocol = NearbyLocal
        reactor.listenTCP(8002, f, interface="127.0.0.1")

        # Start up a web server to provide the software to other clients
        reactor.listenTCP(8003, server.Site(static.File('dist/')))

        # Advertise the node to the network
        reactor.callLater(.1, self.advertise)

        # Create a taskbar icon
        OsSpecific.TaskbarApplet(self.stop, self, outbound_nodes)

        # Start Twisted
        reactor.run()

    def stop(self, *args):
        log.info("Shutting down ....")
        discover.server.close()
        reactor.stop()


if __name__ == '__main__':      
    myService = NearbyService()    
    myService.start()
    
# vim:set ts=4 sw=4 expandtab ai:
