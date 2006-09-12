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

import pygtk
pygtk.require("2.0")
import gtk
import egg.trayicon
import os
import re

from plugin import Plugin

class TaskbarApplet:
    def __init__(self, quit_cb, nearbyInstance, outbound_nodes):
        self.quit_cb = quit_cb
        self.nearbyInstance = nearbyInstance
        self.outbound_nodes = outbound_nodes

        tray_icon = egg.trayicon.TrayIcon("Nearby")
        eventbox = gtk.EventBox()

        tray_icon.add(eventbox)

        img = gtk.Image()
        img.set_from_file("pixmaps/main.ico")
        eventbox.add(img)

        tray_icon.connect("button_press_event", self.popup)
        tray_icon.show_all()

    def popup(self, widget, event):
        self.populate_menu()
        self.popup_menu.popup(None,None,None,event.button,event.time)

    def populate_menu(self):
        self.popup_menu = gtk.Menu()

        # Get a list of subservices
        subservices = []
        for ip,data in self.outbound_nodes.iteritems():
            specific_subservices = data["subservices"]
            for subservice in specific_subservices:
                if subservice[0] not in subservices:
                    subservices.append(subservice[0])
            
	    # Create a label for each entry in the subservices list
        for subservice in subservices:
            menu_item = gtk.MenuItem(subservice.capitalize())
            menu_item.connect('activate', self.service_cb)
            self.popup_menu.append(menu_item)
        
        # Add items for the items only on your hard drive
        no_local_services = True
        for file in os.listdir("plugins/"):
            pluginRe = re.compile("([^-]+)-(.*)")
            result = pluginRe.match(file)
            if result is not None:
                subservice,version = result.groups()
                if subservice not in subservices:
                    menu_item = gtk.MenuItem(subservice.capitalize())
                    menu_item.connect('activate', self.service_cb)
                    self.popup_menu.append(menu_item)
                    no_local_services = False

        # Create a label to notify the user if no services exist    
        if subservices == [] and no_local_services:
            menu_item = gtk.MenuItem("No Services")
            menu_item.set_sensitive(False)
            self.popup_menu.append(menu_item)

        separator = gtk.SeparatorMenuItem()
        self.popup_menu.append(separator)
        
    	# Create an exit option
        menu_item = gtk.MenuItem('Quit')
        menu_item.connect('activate', self.quit)
        self.popup_menu.append(menu_item)
        
        self.popup_menu.show_all()

    def service_cb(self, widget):
        Plugin(widget.get_children()[0].get_text(), self.outbound_nodes)

    def quit(self, *args):
        self.quit_cb(self.nearbyInstance)

def getName():
    """Returns the username of the current user."""
    return os.getenv("LOGNAME")

# vim:set ts=4 sw=4 expandtab ai:
