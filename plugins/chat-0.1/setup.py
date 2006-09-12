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

from distutils.core import setup
import py2exe
import glob

opts = {
	"py2exe": {
		"includes" : "pango,atk,gobject",
        "dll_excludes": [
        "iconv.dll","intl.dll","libatk-1.0-0.dll",
        "libgdk_pixbuf-2.0-0.dll","libgdk-win32-2.0-0.dll",
        "libglib-2.0-0.dll","libgmodule-2.0-0.dll",
        "libgobject-2.0-0.dll","libgthread-2.0-0.dll",
        "libgtk-win32-2.0-0.dll","libpango-1.0-0.dll",
        "libpangowin32-1.0-0.dll"],
	}
       }

setup(
    name="Nearby",
    description="An application to create a high availability local network",
    version="1.0",
    windows = [
    	{"script" : "main.py",
	"icon_resources" : [(1, "main.ico")]}
	],
    options = opts,
    data_files=[("main.ico"),
    		("chat.glade"),
    		]
)
