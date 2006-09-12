"""Taken from: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/334779"""

import sys
import win32gui
import winxpgui

GWL_WNDPROC = -4
GWL_EXSTYLE = -20
IDI_APPLICATION = 32512
LWA_ALPHA = 0x02
WM_TASKBARCREATED = win32gui.RegisterWindowMessage('TaskbarCreated')
WM_USER = 1024
WM_TRAYMESSAGE = WM_USER + 20
WS_EX_LAYERED = 0x80000

class GTKWin32Ext:

    def __init__(self, gtk_window):

        self._window = gtk_window
        self._hwnd = gtk_window.window.handle

        self._message_map = {}

        # Windows transparency is only supported windows2000 and above.
        if sys.getwindowsversion()[0] <= 4:
            self.alpha = None
        else:
            self.alpha = 100
            self._transparency = False

        self.notify_icon = None            

        # Sublass the window and inject a WNDPROC to process messages.
        self._oldwndproc = win32gui.SetWindowLong(self._hwnd, GWL_WNDPROC,
                                                  self._wndproc)

        gtk_window.connect('unrealize', self.remove)


    def add_notify_icon(self, hicon=None, tooltip=None):
        """ Creates a notify icon for the gtk window. """
        if not self.notify_icon:
            if not hicon:
                hicon = win32gui.LoadIcon(0, IDI_APPLICATION)
            self.notify_icon = NotifyIcon(self._hwnd, hicon, tooltip)

            # Makes redraw if the taskbar is restarted.   
            self.message_map({WM_TASKBARCREATED: self.notify_icon._redraw})


    def message_map(self, msg_map={}):
        """ Maps message processing to callback functions ala win32gui. """
        if msg_map:
            if self._message_map:
                duplicatekeys = [key for key in msg_map.keys()
                                 if self._message_map.has_key(key)]
                
                for key in duplicatekeys:
                    new_value = msg_map[key]
                    
                    if isinstance(new_value, list):
                        raise TypeError('Dict cannot have list values')
                    
                    value = self._message_map[key]
                    
                    if new_value != value:
                        new_value = [new_value]
                        
                        if isinstance(value, list):
                            value += new_value
                        else:
                            value = [value] + new_value
                        
                        msg_map[key] = value
            self._message_map.update(msg_map)


    def message_unmap(self, msg, callback=None):
        if self._message_map.has_key(msg):
            if callback:
                cblist = self._message_map[key]
                if isinstance(cblist, list):
                    if not len(cblist) < 2:
                        for i in range(len(cblist)):
                            if cblist[i] == callback:
                                del self._message_map[key][i]
                                return
            del self._message_map[key]


    def remove(self, *args):
        self._message_map = {}
        self.remove_notify_icon()
        self = None
        

    def remove_notify_icon(self):
        """ Removes the notify icon. """
        if self.notify_icon:
            self.notify_icon.remove()
            self.notify_icon = None
            

    def remove(self, *args):
        """ Unloads the extensions. """
        self._message_map = {}
        self.remove_notify_icon()
        self = None            
            

    def show_balloon_tooltip(self, title, text, timeout=10,
                             icon=win32gui.NIIF_NONE):
        """ Shows a baloon tooltip. """
        if not self.notify_icon:
            self.add_notifyicon()
        self.notify_icon.show_balloon(title, text, timeout, icon)


    def set_alpha(self, alpha=100, colorkey=0, mask=False):
        """ Sets the transparency of the window. """
        if self.alpha != None:
            if not self._transparency:
                style = win32gui.GetWindowLong(self._hwnd, GWL_EXSTYLE)
                if (style & WS_EX_LAYERED) != WS_EX_LAYERED:
                    style = style | WS_EX_LAYERED
                    win32gui.SetWindowLong(self._hwnd, GWL_EXSTYLE, style)
                self._transparency = True

            if mask and colorkey:
                flags = LWA_COLORKEY
            else:
                flags = LWA_ALPHA
                if colorkey:
                    flags = flags | LWA_COLORKEY

            win_alpha = int(float(alpha)/100*255)
            winxpgui.SetLayeredWindowAttributes(self._hwnd, colorkey,
                                                win_alpha, flags)
            self.alpha = int(alpha)


    def _wndproc(self, hwnd, msg, wparam, lparam):
        """ A WINDPROC to process window messages. """
        if self._message_map.has_key(msg):
            callback = self._message_map[msg]
            if isinstance(callback, list):
                for cb in callback:
                    apply(cb, (hwnd, msg, wparam, lparam))
            else:
                apply(callback, (hwnd, msg, wparam, lparam))

        return win32gui.CallWindowProc(self._oldwndproc, hwnd, msg, wparam,
                                       lparam)
                
                                    

class NotifyIcon:

    def __init__(self, hwnd, hicon, tooltip=None):

        self._hwnd = hwnd
        self._id = 0
        self._flags = win32gui.NIF_MESSAGE | win32gui.NIF_ICON
        self._callbackmessage = WM_TRAYMESSAGE
        self._hicon = hicon
  
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, self._get_nid())
        if tooltip: self.set_tooltip(tooltip)


    def _get_nid(self):
        """ Function to initialise & retrieve the NOTIFYICONDATA Structure. """
        nid = (self._hwnd, self._id, self._flags, self._callbackmessage,
               self._hicon)
        nid = list(nid)

        if not hasattr(self, '_tip'): self._tip = ''
        nid.append(self._tip)

        if not hasattr(self, '_info'): self._info = ''
        nid.append(self._info)
            
        if not hasattr(self, '_timeout'): self._timeout = 0
        nid.append(self._timeout)

        if not hasattr(self, '_infotitle'): self._infotitle = ''
        nid.append(self._infotitle)
            
        if not hasattr(self, '_infoflags'):self._infoflags = win32gui.NIIF_NONE
        nid.append(self._infoflags)

        return tuple(nid)
        
    
    def remove(self):
        """ Removes the tray icon. """
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self._get_nid())


    def set_tooltip(self, tooltip):
        """ Sets the tray icon tooltip. """
        self._flags = self._flags | win32gui.NIF_TIP
        self._tip = tooltip
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, self._get_nid())
        
        
    def show_balloon(self, title, text, timeout=10, icon=win32gui.NIIF_NONE):
        """ Shows a balloon tooltip from the tray icon. """
        self._flags = self._flags | win32gui.NIF_INFO
        self._infotitle = title
        self._info = text
        self._timeout = timeout * 1000
        self._infoflags = icon
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, self._get_nid())

    def _redraw(self, *args):
        """ Redraws the tray icon. """
        self.remove
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, self._get_nid())



