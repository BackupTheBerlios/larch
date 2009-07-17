#!/usr/bin/env python
#
# uibase.py
#
# (c) Copyright 2009 Michael Towers (larch42 at googlemail dot com)
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
# 2009.06.07

"""This is the base module of the user interface.
It is run in a separate thread from the actual larch program.
"""
import gtk, gobject
import os


class UIbase:
    def __init__(self):
        gobject.threads_init()

        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(base_dir,
                "modules/gtk/larch.glade"))
        self.widget = self.builder.get_object


    def init2(self):
        signals = { "on_window_destroy" : gtk.main_quit }
        signals.update(self.projectpage.signals)
#TODO: waiting for the other modules ...

        self.builder.connect_signals(signals)

        self.window = self.widget("window")
        self.window.show()

        #self.entrydialog = self.widget("dialog_entry")
        #self.entry = self.widget("d_entry")
        #self.entry.set_activates_default(True)


    def add_idle_task(self, function, arg=None):
        gobject.idle_add(self.idle_helper, function, arg)


    def idle_helper(self, function, arg):
        function(arg)
        return False


    def main_loop(self):
        gtk.main()


    def popup_entrydialog(self):
#TODO: I probably want to customize the text, maybe give it a title.
        dlg = gtk.Dialog('Enter New Value')
        dlg.show()

        label = gtk.Label(_("Here:"))
        label.show()
        entry = gtk.Entry()
        entry.show()
        entry.set_activates_default(True)
        dlg.vbox.pack_start(label)
        dlg.vbox.pack_start(entry)

        dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        dlg.set_default_response(gtk.RESPONSE_OK)
        response = dlg.run()
        text = entry.get_text()

        if response == gtk.RESPONSE_OK:
            return text.strip()
        dlg.destroy()
        return None

"""
        res = self.entrydialog.run()
        text = self.entry.get_text()
        self.entrydialog.hide()
        if res == 1:
            return text.strip()
        else:
            return None
"""

