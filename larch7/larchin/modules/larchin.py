#!/usr/bin/env python
#
# larchin.py
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
# 2009.10.15


"""
This is the main module of the larchin program, which should be started with
root priveleges. ????If it is started as a normal user, the actual building
commands will not be exectued, but it might still be useful for debugging.

The actual installation commands are run as a separate process, possibly even
on a different machine (using ssh with public-key authentication). These
installation commands are shell scripts in the package 'larchin-syscalls'.

Also the graphical user interface is run as a separate process and the
communication runs via pipes to the subprocess's stdio channels.
Data is passed as json objects.

???The command-line user interface runs in the same process but a separate
thread is used to dispatch the commands - several commands can be passed
on the command line. The dispatcher waits for one command to complete
before sending the next, so the behaviour should be 'as expected'.

The main loop reads the output from the user interface and acts on the
commands received. Longer running commands, or those needing to run
background process or get information from the user interface, are run
in a separate, 'worker', thread, so that the program remains responsive.

The main work of the program (the installation steps) is handled by the
imported modules, one for each 'stage'.
"""

import os, sys, traceback, signal

import __builtin__

#debugging
__builtin__.dbg_flags = ""
#-

__builtin__.base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append("%s/modules" % base_dir)

from subprocess import Popen, call, PIPE, STDOUT
from optparse import OptionParser
import threading
import json


def errout(text, quit=0):
    sys.stderr.write(text)
    sys.stderr.flush()
    if quit:
        sys.exit(quit)
__builtin__.errout = errout

def debug(text):
    errout("DEBUG: " + text.strip() + "\n")
__builtin__.debug = debug

def bug(text):
    errout("BUG: " + text.strip() + "\n", 1)
__builtin__.bug = bug


import gettext
lang = os.getenv("LANG")
if lang:
    gettext.install('larchin', base_dir+'/i18n', unicode=1)

import welcome, disks, autopart, install
from backend import Backend

class Command:
    def __init__(self):
        """The user interface must already be running before entering here.
        """
        # Used to block further background signal handling while a background
        # thread is running
        self.blocking = False
        # Used to indicate that a background thread was interrupted
        self.breakin = 0

        # Initialize gui modules
        self.pages = []
        for s in (welcome, disks, autopart, install,
                ):
            self.pages.append(s.Stage(len(self.pages)))

        # Connect up the signals and slots
        self.connections = {
                "$$$uiclose$$$": [self._uiclose_clicked],
                "$$$uidoquit$$$": [self._uiclose],
                "$$$uiquit$$$": [self.uiquit],
                "larchin:quit*clicked": [self.uiquit],
                "larchin:cancel*clicked": [self.cancel],
                "log:hide*clicked": [self._activatehidelog],
                "$$$hidelog$$$": [self._activatehidelog],
                "larchin:showlog*toggled": [self._showlog],
                "doc:hide*clicked": [self._activatehidedocs],
                "$$$hidedoc$$$": [self._activatehidedocs],
                "larchin:docs*toggled": [self._showdocs],
                "log:clear*clicked": [self._clearlog],
                "larchin:forward*clicked": [self.next],
            }
        for p in self.pages:
            self.addconnections(p.connect())


    def addconnections(self, connlist):
        for s, f in connlist:
            if self.connections.has_key(s):
                self.connections[s].append(f)
            else:
                self.connections[s] = [f]


    def run(self):
        # Start on the welcome page
        self.pages[0].select_page()
        ui.command("larchin:cancel.enable", False)
        ui.go()


    def next(self):
        self.pages[self.current_page_index].ok()


    def pageswitch(self, index, title):
        ui.command("larchin:stack.set", index)
        self.current_page_index = index
        self.pages[index].init()
        ui.set_stageheader(title)
        ui.command("doc:content.x__html", self.pages[index].getHelp())


    def runsignal(self, sig, *args):
        slots = self.connections.get(sig)
        if slots:
            if ":&" in ":" + sig:
                # Such slots must be run by a background thread
                # Only one at a time is permitted
                self.background(slots, *args)
            else:
                # Normal slots are run directly - they must be quick.
                # They cannot request info from the ui.
                # They should (really!) not run syscall commands.
                for s in slots:
                    s(*args)


    def queuesignal(self, sig, *args):
        """This is called from background code to set up a following
        background demanding ('&') signal, to be called when the current
        one ends.
        """
        if self.bgnext:
            fatal_error("Bug: attempt to queue a second background signal")
        self.bgnext = (sig, args)


    def background(self, *args):
        if self.blocking:
            bug("Attempt to run a second background thread")
            return
        self.blocking = True
        self.pthread = simple_thread(self.worker_run, *args)


    def worker_run(self, slots, *args):
        ui.busy()
        self.breakin = 0
        while self.breakin == 0:
            self.bgnext = None
            try:
                for s in slots:
                    s(*args)
            except:
                if self.breakin == 0:
                    fatal_error("".join(traceback.format_exc()))

            # Check for successor signal
            if self.bgnext == None:
                break
            sig, args = self.bgnext
            slots = self.connections.get(sig)
            if not slots:
                break

        self.blocking = False
        ui.completed(self.breakin == 0)


    def _activatehidelog(self):
        ui.command("larchin:showlog.set", False)


    def _showlog(self, on):
        logger.setVisible(on)


    def _clearlog(self):
        logger.clear()


    def _activatehidedocs(self):
        ui.command("larchin:docs.set", False)


    def _showdocs(self, on):
        ui.command("doc:.setVisible", on)


    def _browse(self, btype, path):
        simple_thread(self._browse_set, btype, path)


    def _browse_set(self, btype, path):
        appcall = config.get(btype)
        while (call(["which", appcall.split()[0]],
                stdout=PIPE, stderr=STDOUT) != 0):
            ok, new = ui.ask("textLineDialog",
                    _("Enter '%s' application ('$' for path argument):") % btype,
                    None, appcall)
            if ok:
                appcall = new
                config.set(btype, appcall)
            else:
                return

        Popen(appcall.replace("$", path) + " &", shell=True)


    def sigint(self, num, frame):
        """CONSOLE MODE ONLY: A handler for SIGINT. Tidy up properly and quit.
        First kill potential running supershell process, then terminate
        logger, and then, finally, terminate the ui process.
        """
        self.uiquit()


    def _uiclose_clicked(self):
        """Called when Window-Close ('X') is clicked in main window.
        """
        ui.confirmDialog(_("Do you really want to quit the program?"),
                async="$$$uidoquit$$$")


    def _uiclose(self, doit):
        """Called when Window-Close ('X') confirmation dialog is closed.
        If doit is True the application should close. The gui itself won't
        be closed until it receives a close command from the main app.
        """
        if doit:
            self.uiquit()


    def uiquit(self):
        self.cancel(True)


    def cancel(self, terminate=False):
# This is a bit experimental - I'm not sure the worker threads will handle
# the break-ins sensibly.
        # This is not called from the worker thread, so it mustn't block.
        self.qthread = simple_thread(self._quit_run, terminate)


    def _quit_run(self, terminate):
        # Kill any running background process
        backend.killprocess()

        if self.blocking:
            # Wait until background process has terminated
            self.pthread.join()
        self.breakin = 0

        ui.progressPopup.end()

        if terminate:
            # Tell the user interface to exit, which will in turn cause the
            # main loop (reading its output) to exit.
            ui.sendui("/")

        else:
            backend.unmount()


    def browser(self, path):
        self._browse("filebrowser", path)


    def chroot(self, cmd, mounts=[]):
        ip = config.ipath()
        if ip != "/":
            for m in mounts:
                self.mount("/" + m, "%s/%s" % (ip, m), "--bind")
            cmd = "chroot %s %s" % (ip, cmd)

        s = supershell(cmd)

        if ip != "/":
            self.unmount(["%s/%s" % (ip, m) for m in mounts])

        if s.ok:
            if s.result:
                return s.result
            else:
                return True
        return False



    def NYI(self):
        ui.infoDialog(_("Function not yet implemented"))


def readfile(f, filter=None):
    fh = open(f)
    r = fh.read()
    fh.close()
    return filter(r) if filter else r

def savefile(f, d):
    fh = open(f, "w")
    r = fh.write(d)
    fh.close()

#TODO: am I using this one?
def config_error(text):
    ui.error(text, _("Configuration Error"))
__builtin__.config_error = config_error

def run_error(text):
    ui.error(text)
__builtin__.run_error = run_error

def fatal_error(text):
    ui.error(text, _("Fatal Error"), fatal=True)
__builtin__.fatal_error = fatal_error

#---------------------------
# Catch all unhandled errors.
def errorTrap(type, value, tb):
    etext = "".join(traceback.format_exception(type, value, tb))
    ui.error(etext, _("This error could not be handled"), fatal=True)

#TODO
#sys.excepthook = errorTrap
#---------------------------


#+++++++++++++++++++++++++++
def mainloop():
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
            command.runsignal(sig, *json.loads(args))

        elif line[0] == "@":
            # The response to an enquiry
            ui.response(line[1:])

        elif line[0] == "/":
            # ui exiting
            exitcode = int(line[1:])

        else:
            fatal_error(_("Unexpected message from ui:\n") + line)


#TODO


    ut = simple_thread(tidyquit)

#---------------------------




def simple_thread(func, *args):
        t = threading.Thread(target=func, args=args)
        t.start()
        return t




def tidyquit():
    backend.unmount()
#???







__builtin__.tt_seedocs = _("See documentation for further details")




if __name__ == "__main__":

    if os.getuid() != 0:
        errout(_("You need to run larchin as root!\n  - otherwise"
                " the installation cannot be carried out.\n"))
        sys.exit(1)

    parser = OptionParser(usage="usage: %prog [options] ['cmd1'] ['cmd2'] ...")
    parser.add_option("-u", "--ui", action="store", type="string", dest="ui",
            default="pyqt", help=_("Select user interface %s") % "(cli, pyqt)",
            metavar="UI")
    parser.add_option("-c", action="store_const", const="cli", dest="ui",
            help=_("Command line interface"))
    parser.add_option("-x", action="store_false", dest="prompt", default=True,
            help=_("Don't wait for confirmation"))
    parser.add_option("-l", action="store_false", dest="logging", default=True,
            help=_("Don't display logging in command line interface"))

    parser.add_option("-r", "--remote", action="store", type="string",
            dest="host", help=_("Remote installation"), metavar="TARGET")
    (options, args) = parser.parse_args()

    # Various ui toolkits could be supported, but at the moment there
    # is only support for pyqt (apart from the console)

    host = options.host



    if options.ui == "cli":
        from console import Ui, Logger, DocViewer
        guiexec = None
    else:
        from gui import Ui, Logger, DocViewer
        if options.ui == "pyqt":
            guiexec = [base_dir + "/modules/pyqt/guibuild.py"]
        else:
            errout(_("ERROR: Unsupported ui option - '%s'\n") % options.ui)
            sys.exit(1)

    __builtin__.ui = Ui(guiexec)
    __builtin__.logger = Logger()
    # Build the documentation viewer
    doc = DocViewer()
    __builtin__.backend = Backend(host)
#???
#    __builtin__.installation = Installation()

    __builtin__.command = Command()

    for p in command.pages:
        p.setup()

    signal.signal(signal.SIGINT, command.sigint)

    command.run()
    mainloop()

    sys.exit(exitcode)
