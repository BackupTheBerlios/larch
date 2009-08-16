#!/usr/bin/env python
#

import sys
import gtk

class Larchin:

    def on_window1_destroy(self, widget, data=None):
        gtk.main_quit()

    def __init__(self):

        builder = gtk.Builder()
        builder.add_from_file("test.glade")

        self.window = builder.get_object("window1")
        builder.connect_signals(self)

if __name__ == "__main__":
    larchin = Larchin()
    larchin.window.show()
    gtk.main()
