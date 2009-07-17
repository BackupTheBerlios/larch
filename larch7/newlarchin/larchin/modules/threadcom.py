# threadcom.py
#
# (c) Copyright 2009 Michael Towers <gradgrind[at]online[dot]de>
#
# This file is part of the larch project.
#
#    larch is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    larch is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with larch; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#----------------------------------------------------------------------------
# 2009.03.23

import dialogs
import threading


class ThreadMessaging:
    """Allows popup messages to be used from the background thread.
    """
    def __init__(self):
        self.event = threading.Event()


    def wait(self):
        self.event.clear()
        self.event.wait()


    def showWarning(self, text, title="larchin Warning"):
        mainWindow.idle_call(self.popup_cb, dialogs.popupWarning, text, title)
        self.wait()
        return self.popresult


    def showMessage(self, text, title="larchin Message"):
        mainWindow.idle_call(self.popup_cb, dialogs.popupMessage, text, title)
        self.wait()


    def popup_cb(self, dtype, text, title):
        """This is an idle callback, running in the main (gui) thread.
        """
        self.popresult = dtype(text, title)
        self.event.set()

