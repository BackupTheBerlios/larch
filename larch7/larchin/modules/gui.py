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
# 2009.09.28

import os, pwd
import json
import threading
from subprocess import Popen, PIPE
import locale


def chid():
    """Drop root privileges and reset the home-directory.
    """
    try:
        # Seems to fail when run from mc shell
        user = os.getlogin()
    except:
        # This will give the wrong name (root) if started via 'su -c'
        user = os.environ["USER"]

    pwdinfo = pwd.getpwnam(user)
    # pwdinfo[0] is user name
    # pwdinfo[2] is uid
    # pwdinfo[3] is gid
    # pwdinfo[5] is home dir
    os.environ["HOME"] = pwdinfo[5]
    os.environ["XAUTHORITY"]=pwdinfo[5] + "/.Xauthority"
    os.setgid(pwdinfo[3])
    os.setuid(pwdinfo[2])


class Ui:
    def __init__(self, guiexec):
        self.answer_event = threading.Event()
        self.answer_event.set()
        self.answer = None

        self.process_lock = threading.Lock()

        self.guiprocess = Popen(guiexec, cwd=base_dir, preexec_fn= chid,
                stdin=PIPE, stdout=PIPE)


#???
    def go(self):
        return


    def getline(self):
        return self.guiprocess.stdout.readline()


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
        To be used in the background thread (only '&'-signals!).
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


    def response(self, text):
        if self.answer_event.is_set():
            fatal_error(_("Unexpected response from ui:\n") + text)
        self.answer = json.loads(text)
        self.answer_event.set()


    def sendui(self, line):
        """Send a text line to the user interface process.
        """
        self.process_lock.acquire()
        try:
            self.guiprocess.stdin.write("%s\n" % line)
        except:
            errout("ui dead (%s)\n" % line)
        self.process_lock.release()


    def infoDialog(self, message, title=None):
        self.ask("infoDialog", message, title)
        return True


    def confirmDialog(self, message, title=None):
        return self.ask("confirmDialog", message, title)


    def error(self, message, title=None, fatal=False):
        self.sendui("_!_ " + json.dumps((fatal, message, title)))


    def busy(self):
        self.command(":larchin.busy", ":stack", True)
        self.command(":cancel.enable", True)


    def completed(self, ok):
        self.command(":cancel.enable", False)
        self.command(":larchin.busy", ":stack", False)



class Logger:
    def __init__(self):
#TODO: This is experimental - it is intended to work around problems arising
#      when the system encoding is not utf8.
        self.encoding = locale.getdefaultlocale()[1]
        if self.encoding == "UTF8":
            self.encoding = None

    def setVisible(self, on):
        ui.command("log:log.setVisible", on)

    def clear(self):
        ui.command("log:logtext.set")

    def addLine(self, line):
#TODO: This is experimental - it is intended to work around problems arising
#      when the system encoding is not utf8.
        if self.encoding:
            line = line.decode(self.encoding, "replace").encode("UTF8")
        ui.command("log:logtext.append_and_scroll", line)

    def undo(self):
        ui.command("log:logtext.undo")

    def quit(self):
        return
