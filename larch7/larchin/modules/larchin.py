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
# 2009.11.23


"""
This is the main module of the larchin program, which must be started with
root priveleges - unless performing a remote installation via ssh.

The actual installation commands are run as a separate process, possibly even
on a different machine (using ssh with public-key authentication). These
installation commands are shell scripts in the package 'larchin-syscalls'.

Also the graphical user interface is run as a separate process and the
communication runs via pipes to the subprocess's stdio channels.
Data is passed as json objects.


???NYI: The command-line user interface runs in the same process but a separate
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

from backend import Backend

class Command:
    def __init__(self):
        # The user interface must already be running before entering here.

        self.current_page_index = 0
        self.pagehistory = []

        # Used to block further background signal handling while a
        # background thread is running
        self.blocking = False
        self.blocking_lock = threading.Lock()
        # A single-entry queue for background signals
        self.bgnext = None
        # Used to indicate that a background thread was interrupted
        self.breakin = 0

        # Connect up the signals and slots
        self.addconnections([
                ("$$$uiclose$$$", self._uiclose_clicked),
                ("$$$uidoquit$$$", self._uiclose),
                ("$$$uiquit$$$", self.uiquit),
                ("larchin:quit*clicked", self.uiquit),
                ("larchin:cancel*clicked", self.cancel),
                ("larchin:forward*clicked", self.next),
                ("larchin:goback*clicked", self.previous),
           ])


    def addconnections(self, connlist):
        for s, f in connlist:
            ui.addslot(s, f)


    def makepages(self):
        # Initialize gui modules
        import welcome, disks, autopart, install, rootpw, grub, done
        self.pages = []
        for s in (welcome, disks, autopart, install, rootpw, grub,
                done):
            stage = s.Stage(len(self.pages))
            self.pages.append(stage)
            self.addconnections(stage.connect())


    def run(self):
        # Start on the welcome page
        ui.command("larchin:cancel.enable", False)
        ui.go()
        ui.sendsignal("&welcome!")


    def next(self):
        self.pages[self.current_page_index].ok()


    def previous(self):
        if len(self.pagehistory) <= 1:
            return
        self.pagehistory.pop()
        ui.sendsignal(self.pagehistory[-1] + "-", False)


    def pageswitch(self, index, title):
        ui.command("larchin:stack.set", index)
        self.current_page_index = index
        ui.set_stageheader(title)
        ui.command("doc:content.x__html", self.pages[index].getHelp())
        self.pages[index].init()


    def background(self, *args):
        self.blocking_lock.acquire()
        queued = False
        if self.blocking:
            if self.bgnext:
                fatal_error("Bug: attempt to queue a second background signal")
            self.bgnext = args
            queued = True
        self.blocking = True
        self.blocking_lock.release()
        if queued:
            return
        self.pthread = self.simple_thread(self.worker_run, *args)


    def worker_run(self, slots, *args):
        ui.busy()
        self.breakin = 0
        while True: # Use a loop to handle queued signals easily
            try:
                for s in slots:
                    s(*args)
            except:
                if self.breakin == 0:
                    fatal_error("".join(traceback.format_exc()))

            # Check for successor signal
            self.blocking_lock.acquire()
            if self.bgnext:
                slots = self.bgnext[0]
                args = self.bgnext[1:]
                self.bgnext = None
                done = (self.breakin != 0) or not slots
            else:
                done = True
            if done:
                ui.completed(self.breakin == 0)
                self.blocking = False
            self.blocking_lock.release()
            if done:
                break


#???
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
        self.qthread = self.simple_thread(self._quit_run, terminate)

    def _quit_run(self, terminate):
        # Kill any running background process
        backend.killprocess()

        if self.blocking:
            # Wait until background process has terminated
            self.pthread.join()
        self.breakin = 0

        ui.progressPopup.end()

        # Do 'unmount' if possible, and quit the backend if terminating
        backend.tidy(terminate)

        if terminate:
            # Tell the user interface to exit, which will in turn cause the
            # main loop (reading its output) to exit.
            ui.sendui("/")


    def simple_thread(self, func, *args):
        t = threading.Thread(target=func, args=args)
        t.start()
        return t


    def readfile(self, path):
        try:
            if path[0] != "/":
                path = base_dir + "/data/" + path
            fh = open(os.path.join(base_dir, path))
            ft = fh.read()
            fh.close()
        except:
            run_error(_("Couldn't read file '%s'") % path)
            return ""
        return ft


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

sys.excepthook = errorTrap
#---------------------------


#+++++++++++++++++++++++++++

def plog(line=None):
    """The lines should not be newline-terminated.
    """
    plog_lock.acquire()
    if line == None:
        logger.clear()
        line = "---*** Log cleared ***---"
    else:
        logger.addLine(line)
    logfile.write(line + '\n')
    plog_lock.release()
__builtin__.plog = plog

#---------------------------

def tidyquit():
    #debug("Tidying up before quitting")
    backend.unmount()


__builtin__.tt_seedocs = _("See documentation for further details")


if __name__ == "__main__":
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

    parser.add_option("-d", "--debug", action="store", type="string",
            default="", dest="dbg", help=_("Debug flags %s") % "[Pfi]",
            metavar="FLAGS")
    (options, args) = parser.parse_args()

#debugging
    __builtin__.dbg_flags = options.dbg
#-
    host = options.host
    if (host != "") and (os.getuid() != 0):
        errout(_("You need to run larchin as root!\n  - otherwise"
                " the installation cannot be carried out.\n"))
        sys.exit(1)

    # Various ui toolkits could be supported, but at the moment there
    # is only support for pyqt (apart from the console)
    if options.ui == "cli":
        from console import Ui, Logger
        guiexec = None
    else:
        from gui import Ui, Logger
        if options.ui == "pyqt":
            guiexec = "quip"
        else:
            errout(_("ERROR: Unsupported ui option - '%s'\n") % options.ui)
            sys.exit(1)

    __builtin__.ui = Ui(guiexec)
    plog_lock = threading.Lock()
    logfile = open("/tmp/larchin_log", "w")
    logger = Logger()
    __builtin__.backend = Backend(host)
    __builtin__.command = Command()
    if not backend.init():
        sys.exit(1)
    command.makepages()
    signal.signal(signal.SIGINT, command.sigint)

    command.run()
    exitcode = ui.mainloop()

    logfile.close()
    sys.exit(exitcode)
