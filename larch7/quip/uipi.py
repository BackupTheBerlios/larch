# uipi.py
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
# 2009.11.02

"""This is an example of an interface class to the larch text-line
based ui toolkit (telibut!?).

It includes a very simple signal-slot mechanism, which can easily be
overridden.
"""

from subprocess import Popen, PIPE, STDOUT
import threading
import json


class Uipi:
    def __init__(self, uiexec):
        # A dict for query tags (see 'Uipi.ask')
        self.query = {}
        # A dict to connect signals to slots. Note that the values
        # are lists of slots, not single slots.
        self.signal_dict = {}
        # Start ui process
        self.uiprocess = Popen(uiexec, stdin=PIPE, stdout=PIPE)


    def addslot(self, signal, function):
        if self.signal_dict.has_key(signal):
            self.signal_dict[signal].append(function)
        else:
            self.signal_dict[signal] = [function]


    def sendsignal(self, name, *args):
        # When there are no slots the signal is simply ignored.
        for slot in self.signal_dict.get(name, []):
            slot(*args)


    def uipi_error(self, text):
        """This method provides a simple means of outputting an error
        report, assuming of course that stderr goes somewhere and is visible!
        It might be better to throw an exception, but the advantage of this
        function is that it doesn't disrupt the normal course of events.
        Override it if you want something else to happen.
        """
        sys.stderr.write(text)
        sys.stderr.flush()


    def mainloop(self):
        """Loop to read input from ui and act on it.
        """
        global exitcode
        exitcode = 0
        while True:
            line = ui.getline()
            if not line:
                # Occurs when the ui process has exited
                break

            elif line[0] == "^":
                # signal, call slots
                sig, args = line[1:].split(None, 1)
                self.sendsignal(sig, *json.loads(args))

            elif line[0] == "@":
                # The response to an enquiry
                ui.response(line[1:])

            elif line[0] == "/":
                # ui exiting
                exitcode = int(line[1:])

            else:
                uipi_error("Unexpected message from ui:\n" + line)

        return exitcode


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


    def asknowait(self, cmd, signal, *args):
        """Send a request for information to the user interface.
        The method returns immediately without a response, which is sent
        later by means of the signal.
        The command is of the form 'widget.method', 'args' is the list of
        arguments. The argument list is encoded as json for transmission.
        'signal' is the name of the signal to be sent to return the result
        of the enquiry when it is available.
        """
        c = "?%s:%s" % (signal, cmd)
        if args:
            c += " " + json.dumps(args)
        self.sendui(c)
        return None


    def ask(self, cmd, *args):
        """Send a request for information to the user interface.
        This method waits until the result has been received, which means:
        *** WARNING *** It may not be called within the same thread as
        the main loop, or else the whole interface will hang.
        Thus care should be exercised when using this method.

        The command is of the form 'widget.method', 'args' is the
        list of arguments. The argument list is encoded as json for
        transmission.
        """
        event = AskEvent()
        self.query[event.tag] = event
        c = "?%s:%s" % (event.tag, cmd)
        if args:
            c += " " + json.dumps(args)
        self.sendui(c)
        event.wait()
        del(self.query[event.tag])
        return event.answer


    def response(self, text):
        l, r = text.split(":", 1)
        a = json.loads(r)
        if self.query.has_key(l):
            self.query[l].set(a)
        else.
            self.sendsignal(l, a)


    def widget(self, wtype, wname, **args):
        """Define a new widget.
        """
        self.sendui("%%%s %s %s" % (wtype, wname, json.dumps(args)))


    def layout(self, wname, ltree):
        """Layout a widget.
        Essentially this means specifying the layout of the widget's
        sub-widgets within the named widget.
        """
        self.sendui("$%s %s" % (wname, json.dumps(ltree)))


    def sendui(self, line):
        """Send a text line to the user interface process.
        """
        self.process_lock.acquire()
        try:
            self.guiprocess.stdin.write("%s\n" % line)
        except:
            errout("ui dead (%s)\n" % line)
        self.process_lock.release()


    def infoDialog(self, message, title=None, async=""):
        if title == None:
            title = _("Information")
        if async:
            return self.asknowait("infoDialog", async, message, title)
        return self.ask("infoDialog", message, title)


    def confirmDialog(self, message, title=None, async=""):
        if title == None:
            title = _("Confirmation")
        if async:
            return self.asknowait("confirmDialog", async, message, title)
        return self.ask("confirmDialog", message, title)


    def error(self, message, title=None, fatal=False):
        if title == None:
            title = _("Error")
        self.command("errorDialog" if fatal else "warningDialog",
            message, title)



class AskEvent:
    """Generate a tagged threading.Event which can store a response object.
    """
    count = 0

    def __init__(self):
        self.event = threading.Event()
        self.tag = str(AskEvent.count)
        AskEvent.count +=1

    def wait(self):
        self.event.wait()

    def set(self, a):
        self.answer = a
        self.event.set()
