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

import os
import re
import random
import urllib
import zipfile
import logging

log = logging.getLogger("nearby")

class Plugin:
    def __init__(self, subservice, outbound_nodes):
        self.subservice = subservice.lower()
        self.outbound_nodes = outbound_nodes

        # Determine the greatest version of the subservice available on the
        # network
        self.version = 0
        for file in os.listdir("plugins/"):
            pluginRe = re.compile("([^-]+)-(.*)")
            result = pluginRe.match(file)
            if result is not None and result.groups()[0] == self.subservice:
                subservice,version = result.groups()
                self.version = version
                break

        for ip,data in outbound_nodes.iteritems():
            for subservice,version in data["subservices"]:
                if subservice == self.subservice:
                    if self.version < float(version):
                        self.version = float(version)
        
        if self.execute() == False:
            # If we get here then the plugin has not been installed
            # Install it and then execute it.
            self.fetch()
            self.execute()
    
    def execute(self):
        # If we are in Windows, execute the compiled version
        if os.path.isfile("plugins/%s-%s/main.exe" % (self.subservice, self.version)):
            os.spawnl(os.P_NOWAIT, "plugins/%s-%s/main.exe" % (self.subservice, self.version))
            return True

        # Otherwise we are in Linux so we should invoke the python interpreter
        print "plugins/%s-%s/main.py" % (self.subservice, self.version)
        if os.path.isfile("plugins/%s-%s/main.py" % (self.subservice, self.version)):
            os.spawnlp(os.P_NOWAIT, "python", "python", "plugins/%s-%s/main.py" % (self.subservice, self.version))
            return True
            
        return False
    def fetch(self):
        # Find all of the nodes which have this version of the subservice
        available_nodes = []
        for ip,data in self.outbound_nodes.iteritems():
            for subservice,version in data["subservices"]:
                if subservice == self.subservice and float(version) == self.version:
                    available_nodes.append(ip)
        
        # Randomly choose one from the list
        selected_node = random.choice(available_nodes)
        
        # Download the package using the webserver which is running on port
        # 8003 on each client
        remote_file = urllib.urlopen("http://%s:8003/%s-%s.zip" % (selected_node, self.subservice, self.version))
        saved_file = open("dist/%s-%s.zip" % (self.subservice, self.version), "wb")
        while 1:
            data = remote_file.read(8192)
            if not data:
                break
            saved_file.write(data)
        remote_file.close()
        saved_file.close()

        # Determine which operating system we are running
        import platform
        try:
            platform.win32_ver()
            operating_system = "windows"
        except:
            operating_system = "linux"
            
        # Extract the correct directory from the zip file to the plugin
        # directory. Taken from: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/252508
        if not os.path.exists("plugins/%s-%s/" % (self.subservice, self.version)):
            os.mkdir("plugins/%s-%s/" % (self.subservice, self.version))

        zf = zipfile.ZipFile("dist/%s-%s.zip" % (self.subservice, self.version),)

        for i, name in enumerate(zf.namelist()):
            if not name.endswith("/") and name.startswith(operating_system):
                outfile = open(os.path.join("plugins","%s-%s" % (self.subservice, self.version), name[len(operating_system)+1:]), "wb")
                outfile.write(zf.read(name))
                outfile.flush()
                outfile.close()

# vim:set ts=4 sw=4 expandtab ai:
