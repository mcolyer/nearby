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

import gtk
import gobject
import time
import win32gtkgui
import win32gui
import win32con
import os
import re
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205

from plugin import Plugin

class TaskbarApplet:
    def __init__(self, quit_cb, nearbyInstance, outbound_nodes):
        #Setup some callbacks so that the applet can stop the server
        self.quit_cb = quit_cb
        self.nearbyInstance = nearbyInstance
        self.outbound_nodes = outbound_nodes
        
        self.main_loop = gobject.MainLoop()
        
        # Create a hidden window in order to create a gtk handle
        self.wnd = gtk.Window()
        self.wnd.realize()

        # Connect up the nasty win32 stuff
        self.win32ext = win32gtkgui.GTKWin32Ext(self.wnd)

	hinst = win32gui.GetModuleHandle(None)
	icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
	hicon = win32gui.LoadImage(hinst, "pixmaps/main.ico", win32con.IMAGE_ICON, 0, 0, icon_flags)
	self.win32ext.add_notify_icon(hicon, 'Nearby')

        self.populate_menu()

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
        menu_item.connect_object('activate', self.quit, self.wnd)
        self.popup_menu.append(menu_item)
        
        self.popup_menu.show_all()
        self.win32ext.notify_icon.menu = self.popup_menu

        # Set up the callback messages
        self.win32ext.message_map({
        win32gtkgui.WM_TRAYMESSAGE: self.on_notifyicon_activity
        })                
        
    def on_notifyicon_activity(self, hwnd, message, wparam, lparam):
	self.populate_menu()
        if lparam == WM_RBUTTONUP:
            self.win32ext.notify_icon.menu.popup(None, None, None, 0, 0)
        elif lparam == WM_LBUTTONUP:
            self.win32ext.notify_icon.menu.popdown()            

    def service_cb(self, widget):
        Plugin(widget.get_children()[0].get_text(), self.outbound_nodes)
	
    def quit(self, *args):
        self.win32ext.remove_notify_icon()
        
        # Callback on the main service and tell it to quit
        self.quit_cb(self.nearbyInstance)

def getName():
    """Returns the name of the current user."""
    return os.getenv("USERNAME")
