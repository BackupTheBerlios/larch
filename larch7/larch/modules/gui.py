#!/usr/bin/env python
#
# gui.py
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
# 2009.09.13

import json
import threading
from subprocess import Popen, PIPE

class Ui:
    def __init__(self, commqueue, flag, guiexec):
        self.queue = commqueue
        self.flag = flag

        self.answer_event = threading.Event()
        self.answer_event.set()
        self.answer = None

        self.guiprocess = Popen(guiexec, cwd=base_dir, stdin=PIPE, stdout=PIPE)
        self.gthread = threading.Thread(target=self.substart)
        self.gthread.start()


    def go(self):
        return


    def substart(self):
        """A thread function for reading input from a subprocess line
        by line. The lines are placed in the communication queue.
        """
        while True:
            line = self.guiprocess.stdout.readline()
            if not line:
                break
            # Pass on the output of the process
            self.queue.put(self.flag + line)

        self.guiprocess.wait()
        self.queue.put("%s/%d\n" % (self.flag, self.guiprocess.returncode))


    def command(self, cmd, *args):
        """Send a command to the user interface.
        The command is of the form 'widget.method', 'args' is the
        list of arguments. The argument list is encoded as json for
        transmission.
        """
        c = "!" + cmd
        if args:
            c += " " + json.dumps(args)
        self.sendui(c)


    def ask(self, cmd, *args):
        """Send a request for information to the user interface.
        To be used in the worker thread (only '&'-signals!).
        The command is of the form 'widget.method', 'args' is the
        list of arguments. The argument list is encoded as json for
        transmission.
        Then wait for the answer and return it as result.
        """
        c = "?" + cmd
        if args:
            c += " " + json.dumps(args)
        if not self.answer_event.is_set():
            fatal_error(_("ui not ready for enquiry:\n") + c)
        self.answer = None
        self.answer_event.clear()
        self.sendui(c)
        self.answer_event.wait()
        return self.answer


    def sendui(self, line):
        """Send a text line to the user interface process.
        """
        try:
            self.guiprocess.stdin.write("%s\n" % line)
        except:
            errout("ui dead (%s)\n" % line)


    def infoDialog(self, message, title=None):
        self.ask("infoDialog", message, title)
        return True


    def confirmDialog(self, message, title=None):
        return self.ask("confirmDialog", message, title)


    def error(self, message, title=None, fatal=False):
        self.sendui("_!_ " + json.dumps((fatal, message, title)))


    def busy(self):
        self.command(":larch.busy", ":notebook", True)
        self.command(":cancel.enable", True)


    def completed(self, ok):
        self.command(":cancel.enable", False)
        self.command(":larch.busy", ":notebook", False)



class Logger:


    def setVisible(self, on):
        ui.command("log:log.setVisible", on)

    def clear(self):
        ui.command("log:logtext.set")

    def addLine(self, line):
        ui.command("log:logtext.append_and_scroll", line)

    def undo(self):
        ui.command("log:logtext.undo")

    def quit(self):
        return
