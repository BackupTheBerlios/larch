#!/usr/bin/env python
#

import sys
import gtk

class Test:

    def on_window1_destroy(self, widget, data=None):
        gtk.main_quit()

    def __init__(self):

        builder = gtk.Builder()
        builder.add_from_file("test.glade")

        self.window = builder.get_object("window1")
        self.mainlist = builder.get_object("liststore1")
        self.cr = builder.get_object("cellrenderercombo1")
        #self.cr.set_property("editable", True)
        self.filter = builder.get_object("treemodelfilter1")
        self.filter.set_visible_column(1)
        builder.connect_signals(self)

    def on_cellrenderercombo1_edited(self, cellrenderertext, path, new_text):
        iter = self.mainlist.get_iter(path)
        self.mainlist.set_value(iter, 0, new_text)


if __name__ == "__main__":
    test = Test()
    test.window.show()
    gtk.main()
