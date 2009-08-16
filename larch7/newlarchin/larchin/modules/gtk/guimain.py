#!/usr/bin/env python
#
# guimain.py - larchin main window
#
# (c) Copyright 2008, 2009 Michael Towers <gradgrind[at]online[dot]de>
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
# 2009.03.20

import gtk, gobject
from dialogs import popupError, popupMessage

def idleWrap(function, args):
    """A wrapper for an idle time call to ensure that it is a one-off call.
    """
    function(*args)
    return False


class Larchin:
    """The main gui class, managing the larchin window.
    """
    def exit(self):
        gtk.main_quit()


    def on_window1_delete_event(self, widget, event, data=None):
        install.cancel()
        install.tidyup()
        return False        # propagate event


    def on_window1_destroy(self, widget, data=None):
        self.exit()


    def mainLoop(self):
        self.window.show()
        gtk.main()


    def on_windowLog_delete_event(self, widget, event, data=None):
        self.logwindow.hide()
        return True        # don't propagate event


    def widget(self, name):
        """Return the widget object corresponding to the widget name from
        the gui defined in the glade file.
        """
        return self.builder.get_object(name)


    def idle_call(self, function, *args):
        """Add a function to be called just once in gui idle time.
        """
        gobject.idle_add(idleWrap, function, args)


    def __init__(self):
        """Set up the gui - the main window and the logger, the latter
        being hidden initially.
        """
        gobject.threads_init()
        self.stage = None

        self.builder = gtk.Builder()
        self.builder.add_from_file(basePath + "/modules/gtk/larchin.glade")

        self.window = self.widget("window1")
        self.mainarea = self.widget("notebook")
        # Hiding the tabs here allows them to be still visible in Glade
        self.mainarea.set_show_tabs(False)
        # Need a table to convert from page name to page index
        self.pages = {}
        for i in range(self.mainarea.get_n_pages()):
            child = self.mainarea.get_nth_page(i)
            label = self.mainarea.get_tab_label_text(child)
            self.pages[label] = i

        self.builder.connect_signals(self)

        # The log viewer
        self.logwindow = self.widget("windowLog")
        self.reportview = self.widget("textviewLog")
        self.reportbuf = self.reportview.get_buffer()
        self.mark = self.reportbuf.create_mark(None,
                self.reportbuf.get_end_iter(), False)

        # Stage list view:
        self.listview = self.builder.get_object("treeviewStages")
        # Stage list model:
        self.liststore = self.builder.get_object("liststoreStages")
        # Set up a callback for when a stage is clicked in the stage list
        self.selection = self.widget("treeviewStages").get_selection()
        self.selection.set_mode(gtk.SELECTION_SINGLE)
        self.selection.connect('changed', self.stageClicked_cb)

        self.okbutton = self.widget("buttonOK")
        self.cancelbutton = self.widget("buttonCancel")

        self.watchcursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
        self.busy = False


    def idle_setWidget(self, widgetname, enable):
        """Given the name of a main area widget, set it as the current
        widget in that area. Also (de)sensitize the OK button and the
        stage list according to the value of 'enable'.

        This must be done as an idle-call because it is called from the
        background thread.
        """
        self.idle_call(setWidget, widgetname, enable)

    def setWidget(self, widgetname, enable):
        self.mainarea.set_current_page(self.pages[widgetname])
        # Set list selection if possible
        i = 0
        for r in self.liststore:
            if (r[2] == name):
                self.selection.select_path(i)
                return
            i += 1
        self.selection.unselect_all()

        # Enable or disable interaction with the OK button and the stage list.
        self.okbutton.set_sensitive(enable)
        self.listview.set_sensitive(enable)
        self.window.set_cursor(None if enable else self.watchcursor)


    def getStageTitle(self, name):
        """Given the name tag of a stage return its title as shown in
        the stage list.
        """
        i = 0
        for r in self.liststore:
            if (r[2] == name):
                return self.liststore[i][0]
            i += 1
        return None


    def report(self, text):
        """An idle callback: add text and a newline to the log window.
        Initiated from the 'plog' function.
        """
        self.reportbuf.insert(self.reportbuf.get_end_iter(), text+'\n')
        self.reportview.scroll_mark_onscreen(self.mark)


    def tick_stage(self, name, set=True):
        """Set the checkbox for the given stage (if the name is in the list).
        """
        i = 0
        for r in self.liststore:
            if (r[2] == name):
                self.liststore[i][1] = set
                break
            i += 1


    def on_buttonOK_clicked(self, widget, data=None):
        install.ok_clicked()


    def on_buttonHelp_clicked(self, widget, data=None):
        popupMessage(currentstage.getHelp(), title=_("larchin Help"))


    def on_buttonCancel_clicked(self, widget, data=None):
        install.cancel()


    def on_buttonLog_clicked(self, widget, data=None):
        self.logwindow.show()


    def stageClicked_cb(self, widget, data=None):
        tv, iter = self.selection.get_selected()
        if iter:
            s = self.liststore.get_value(iter, 0)
        else:
            s = None
        install.jumpto(s)
