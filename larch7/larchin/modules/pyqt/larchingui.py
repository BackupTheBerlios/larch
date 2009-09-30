#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# larchingui.py - pyqt version
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
# 2009.09.27

import sys
from PyQt4 import QtGui, QtCore
from guibuild import *


if __name__ == "__main__":
    # Could get the gui files from sys.argv[1:]
    app = QtGui.QApplication([])                            #qt

    import gettext
    lang = os.getenv("LANG")
    if lang:
        gettext.install('larchin', 'i18n', unicode=1)

    class Larchin(GuiApp):
        dummyargs = "[null, []]"
        def __init__(self):
            GuiApp.__init__(self, app)

        def init(self):
            GuiApp.init(self, ["gui.layout.py", "log.layout.py",],
                    __file__.rsplit("/", 2)[0])
            self.logwidget = self.widgets["log:logtext"]
            self.widgets["log:log"].widget.trapclose = self.dohide
            self.widgets[":larchin"].widget.trapclose = self.doquit

        def new_line(self, line):
            text = str(line).strip()

            #DEBUG
            #sys.stderr.write(text+'\n')
            #sys.stderr.flush()

            if text.startswith("_!_"):
                einfo = json.loads(text[3:])
                if einfo[0]:
                    gui_error(*einfo[1:])
                else:
                    gui_warning(*einfo[1:])

            elif text.startswith("!") or text.startswith("?"):
                GuiApp.new_line(self, text)

            elif text.startswith("/"):
                app.quit()

            else:
                self.got(text.rstrip())

        def got(self, line):
            self.logwidget.append_and_scroll(line)

        def dohide(self, *args):
            self.send("^", "$$$hidelog$$$ " + Larchin.dummyargs)
            return True

        def doquit(self, *args):
            if confirmDialog(_("Do you really want to quit the program?")):
                self.send("^", "$$$uiquit$$$ " + Larchin.dummyargs)
            return True

    # We need a global GuiApp instance
    guiapp = Larchin()
    guiapp.init()

    ithread = Input(sys.stdin, guiapp.new_line)
    ithread.start()

    guiapp.show(":larchin")
    app.exec_()                                             #qt

