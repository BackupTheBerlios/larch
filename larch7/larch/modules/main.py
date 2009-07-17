#!/usr/bin/env python
#
# main.py
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
# 2009.06.30

"""This is the main module of the actual larch code, which is started by
the 'larch.py' script as a separate process.

Communication between the initial (root) process ('larch.py') and this one
is via pipes/stdio. Communication with the user interface is via the same
pipes, the root process acting as a switchboard for messages.

The main thread reads the input stream and acts on the received lines.
The main job of the program is handled by the imported modules and run
in a separate thread.
"""

import os, sys

import __builtin__
__builtin__.base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append("%s/modules" % base_dir)

import threading, traceback
import json

import base
__builtin__.config = base.LarchConfig(os.environ["HOME"])

from projectpage import ProjectPage
from installpage import InstallPage


#---------------------------
#def tr(s):
#    return s
#__builtin__._ = tr

import gettext
lang = os.getenv("LANG")
if lang:
    gettext.install('larch', base_dir+'/i18n', unicode=1)
#---------------------------


class Command:
    def __init__(self):
        """The user interface must already be running before entering here.
        """
        self.ostream = sys.stdout
        self.ready = threading.Event()
        self.ready.set()
        self.answer_event = threading.Event()
        self.answer_event.set()
        self.answer = None

        # These are used by 'supershell'
        self.ok = None
        self.result = None

        # Used to block further signal handling while the worker thread
        # is running
        self.blocking = False

        # Initialize gui modules
#TODO: the other pages
        self.pages = [ProjectPage(), InstallPage()]

        # Connect up the signals and slots
        self.connections = {
                "$$$hidelog$$$": [self.activatehidelog],
                ":showlog*toggled": [self.showlog],
                ":notebook*changed": [self.pageswitch],
            }
        for p in self.pages:
            for s, f in p.connect():
                if self.connections.has_key(s):
                    self.connections[s].append(f)
                else:
                    self.connections[s] = [f]


    def run(self):
        # Start on the project page
        self.pages[0].setup()


    def pageswitch(self, index):
        self.pages[index].setup()


    def ui(self, cmd, *args):
        """Send a command to the user interface.
        To be used in the worker thread.
        The command is of the form 'widget.method', 'args' is the
        list of arguments. The argument list is encoded as json for
        transmission.
        """
        c = "!" + cmd
        if args:
            c += " " + json.dumps(args)
        self.send(c)


    def uiask(self, cmd, *args):
        """Send a request for information to the user interface.
        To be used in the worker thread.
        The command is of the form 'widget.method', 'args' is the
        list of arguments. The argument list is encoded as json for
        transmission.
        Then wait for the answer and return it as result.
        """
        c = "?" + cmd
        if args:
            c += " " + json.dumps(args)
        if not self.answer_event.is_set():
            self.fatal(_("ui not ready for enquiry"), c)
        self.answer = None
        self.answer_event.clear()
        self.send(c)
        self.answer_event.wait()
        return self.answer


    def send(self, line):
#TODO: Does this need a lock?
        self.ostream.write("%s\n" % line)
        self.ostream.flush()


    def worker(self, *args):
        self.blocking = True
        self.pthread = threading.Thread(target=self.worker_run, args=args)
        self.pthread.start()


    def worker_run(self, slots, *args):
        self.ui(":larch.busy", ":notebook", True)
        for s in slots:
            s(*args)
        self.blocking = False
        self.ui(":larch.busy", ":notebook", False)


    def supershell(self, cmd, cmdtype=">"):
        """Send a command to the root process and wait until it completes.
        To be used in the worker thread.
        """
        if not self.ready.is_set():
            self.fatal(_("'supershell' called while not ready."))
        self.result = []
        self.ready.clear()
        self.send(cmdtype + cmd.strip())
        self.ready.wait()
        return self


    def activatehidelog(self):
        self.ui(":showlog.set", False)


    def showlog(self, on):
        self.ui("log:log.setVisible", on)


#TODO
    def error(self, etype, message, *args):
        self.send("_!_ " + json.dumps((etype, message) + args))


__builtin__.command = Command()

#TODO
def config_error(text):
    command.error("Warning", text, _("CONFIG_ERROR"))
__builtin__.config_error = config_error


#---------------------------
# Catch all unhandled errors.
def errorTrap(type, value, tb):
    etext = "".join(traceback.format_exception(type, value, tb))
    command.error("Fatal", etext, _("This error could not be handled"))

sys.excepthook = errorTrap
#---------------------------


#+++++++++++++++++++++++++++
def mainloop(fhi):
    """Loop to read input and act on it.
    """
    while True:
        line = fhi.readline()
        if not line:        # Is this at all possible?
            command.fatal(_("Root process died."))
            return

        #DEBUG
        #sys.stderr.write(line)
        #sys.stderr.flush()

        source, text = line.split(":", 1)
        if source == "G":
            if text[0] == "^":
                # signal, call slots
                sig, args = text[1:].split(None, 1)
                arglst = json.loads(args)
                slots = command.connections.get(sig)
                if slots:
                    if sig[0] == "$":
                        # Unblockable slots called from the main loop
                        for s in slots:
                            s(*arglst[1])
                    elif not command.blocking:
                        # Slots called from a separate thread, blockable
                        command.worker(slots, *arglst[1])


            elif text[0] == "@":
                # The response to an enquiry
                if command.answer_event.is_set():
                    command.fatal(_("Unexpected response from ui"), text)
                command.answer = json.loads(text[1:])
                command.answer_event.set()

            else:
                command.fatal(_("Unexpected message from ui"), text)

        elif source == "X":
            if text[0] == "/":
                if command.ready.is_set():
                    command.fatal(_("Unexpected end of 'supershell' process."))
                command.ok = (text[1] == "0")
                command.ready.set()
            elif text[0] == "-":
                command.result.append(text[1:])

        else:
            command.fatal(_("Main process received illegal command"), line)

#---------------------------


if __name__ == "__main__":
    command.run()
    mainloop(sys.stdin)

