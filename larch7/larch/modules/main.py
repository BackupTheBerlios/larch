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
# 2009.08.18

"""This is the main module of the actual larch code, which is started by
the 'larch.py' script as a separate process.

Communication between the initial (root) process ('larch.py') and this one
is via pipes (root process) and stdio (this process). Operations requiring
superuser rights are run as shell scripts via the root process.

The user interface is also run as a separate process and the communication
is also via pipes; data is passed as json objects.

A thread is used to read input from the root process (stdin) and another
thread is used to read input from the user interface. Both these threads
place the lines they receive in a queue which is read by the main thread.
The received lines are then acted upon.

The main job of the program is handled by the imported modules and run
in a separate thread.
"""

import os, sys, traceback, re

import __builtin__
__builtin__.base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append("%s/modules" % base_dir)
script_dir = "%s/buildscripts" % base_dir

from subprocess import Popen, PIPE, STDOUT
import threading, traceback
from Queue import Queue
import json

import base

from projectpage import ProjectPage
from installpage import InstallPage
from buildpage import BuildPage
from mediumpage import MediumPage

def debug(text):
    sys.stderr.write("DEBUG: " + text.strip() + "\n")
    sys.stderr.flush()
__builtin__.debug = debug

import gettext
lang = os.getenv("LANG")
if lang:
    gettext.install('larch', base_dir+'/i18n', unicode=1)


class Command:
    def __init__(self):
        """The user interface must already be running before entering here.
        """
        self.ostream = sys.stdout
        self.ready = threading.Event()
        self.ready.set()
        self.ui_answer_event = threading.Event()
        self.ui_answer_event.set()
        self.ui_answer = None

        # These are used by 'supershell'
        self.ok = None
        self.result = None
        self.breakin = 0

        # Keep a record of mounts
        self.mounts = []

        # Used to block further signal handling while the worker thread
        # is running
        self.blocking = False

        # Initialize gui modules
        self.pages = [ProjectPage(), InstallPage(), BuildPage(), MediumPage()]

        # Connect up the signals and slots
        self.connections = {
                "$$$uiquit$$$": [self._uiquit],
                "$$$hidelog$$$": [self._activatehidelog],
                "$showlog*toggled$": [self._showlog],
                ":notebook*changed": [self._pageswitch],
                "$$$clearlog$$$": [self._clearlog],
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


    def _pageswitch(self, index):
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
        self.sendui(c)


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
        if not self.ui_answer_event.is_set():
            self.fatal(_("ui not ready for enquiry"), c)
        self.ui_answer = None
        self.ui_answer_event.clear()
        self.sendui(c)
        self.ui_answer_event.wait()
        return self.ui_answer


    def sendui(self, line):
        """Send a text line to the user interface process.
        To be used in the worker thread.
        """
        try:
            guiprocess.stdin.write("%s\n" % line)
        except:
            sys.stderr.write("ui dead (%s)\n" % line)
            sys.stderr.flush()


    def log(self, line):
        # The line should not have a newline terminator
        logqueue.put(line)


    def send(self, line):
        self.log(line)
#TODO: Does this need a lock?
        self.ostream.write("%s\n" % line)
        self.ostream.flush()


    def worker(self, *args):
        self.blocking = True
        self.pthread = threading.Thread(target=self.worker_run, args=args)
        self.pthread.start()


    def worker_run(self, slots, *args):
        self.ui(":larch.busy", ":notebook", True)
        try:
            for s in slots:
                s(*args)
        except:
            if self.breakin == 0:
                typ, val, tb = sys.exc_info()
                fatal_error("".join(traceback.format_exception(typ, val, tb)))

        self.blocking = False
        self.ui(":larch.busy", ":notebook", False)


    def supershell(self, cmd, cmdtype=">"):
        """Send a command to the root process and wait until it completes.
        To be used in the worker thread.
        """
        if not self.ready.is_set():
            fatal_error("'supershell' called while not ready.")
        self.result = []
        self.ready.clear()
        self.send(cmdtype + cmd.strip())
        self.ready.wait()

        assert (self.breakin == 0)
        return self


    def _activatehidelog(self):
        # This is not called from the worker thread, but I think it's ok
        self.ui(":showlog.set", False)


    def _showlog(self, on):
        # This is not called from the worker thread, but I think it's ok
        self.ui("log:log.setVisible", on)


    def _clearlog(self):
        # This is not called from the worker thread, but I think it's ok
        self.ui("log:logtext.set")


    def _uiquit(self):
        # This is not called from the worker thread, so it mustn't block.
        self.qthread = simple_thread(self._quit_run)

    def _quit_run(self):
        # Signal to the worker thread that a break is requested
        self.breakin = 1
        # Kill any running supershell process
        self.send(".")

        if self.blocking:
            # Wait until supershell process has terminated
            self.pthread.join()
        self.breakin = 0

        # Tell the user interface to exit, which will in turn cause the
        # thread reading its output to terminate (see function 'gtstart').
        self.sendui("/")


    def mount(self, src, dst, opts):
        if supershell("mount %s %s %s" % (opts, src, dst)).ok:
            self.mounts.append(dst)
            return True
        return False


    def unmount(self, dst=None):
        if dst == None:
            r = True
            for m in list(self.mounts):
                if not self.unmount(m):
                    r = False
            return r

        if supershell("umount %s" % dst).ok:
            self.mounts.remove(dst)
            return True
        return False

    def edit(self, fname, source=None, label=None, filter=None):
        if "/" in fname:
            f = fname
        else:
            f = os.path.join(config.get("profile"), fname)
        if os.path.isfile(f):
            source = readfile(f, filter)
        else:
            assert source != None   # The file must be present
            if source:
                source = readfile(source, filter)
        if not label:
            label = _("Editing '%s'") % fname
        self.ui("editor:label.set", label)
        self.ui("editor:text.set", readfile(f) if os.path.isfile(f)
                else source)
        if self.uiask("editor:editor.showmodal"):
            t = self.uiask("editor:text.get").encode("utf8")
            if t[-1] != "\n":
                t += "\n"
            savefile(f, t)


    def browser(self, path):
        cmd = config.get("filebrowser").replace("%", path)
        #?Popen(cmd, shell=True, stdout=open("/dev/null"), stderr=STDOUT)
        Popen(cmd, shell=True)


    def chroot(self, cmd, mounts=[]):
        ip = config.get("install_path")
        for m in mounts:
            if ip != "/":
                supershell("mount --bind /%s %s/%s" % (m, ip, m))

        if ip != "/":
            cmd = "chroot %s %s" % (ip, cmd)
        s = supershell(cmd)

        for m in mounts:
            if ip != "/":
                supershell("umount %s/%s" % (ip, m))

        if s.ok:
            if s.result:
                return s.result
            else:
                return True
        return False


    def script(self, cmd):
        s = supershell("%s/%s" % (script_dir, cmd))
        if s.ok:
            return ""
        else:
            return "SCRIPT ERROR: (%s)\n" % cmd + "".join(s.result)


    def info(self, message):
        self.uiask("infoDialog", message)


    def error(self, etype, message, *args):
        self.sendui("_!_ " + json.dumps((etype, message) + args))


    def NYI(self):
        self.uiask("infoDialog", _("Function not yet implemented"))


def readfile(f, filter=None):
    fh = open(f)
    r = fh.read()
    fh.close()
    return filter(r) if filter else r

def savefile(f, d):
    fh = open(f, "w")
    r = fh.write(d)
    fh.close()


def config_error(text):
    command.error("Warning", text, _("CONFIG ERROR"))
__builtin__.config_error = config_error

def run_error(text):
    command.error("Warning", text, _("BUILD ERROR"))
__builtin__.run_error = run_error

def fatal_error(text):
    command.error("Fatal", text)
__builtin__.fatal_error = fatal_error

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
        # We may have to wait for a worker thread to finish, hence the
        # following repeated test for the end of a thread after a breakin.
        line = commqueue.get()

        #line = fhi.readline()
        #if not line:        # Is this at all possible?
        #    command.fatal(_("Root process died."))
        #    return

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
                if command.ui_answer_event.is_set():
                    command.fatal(_("Unexpected response from ui"), text)
                command.ui_answer = json.loads(text[1:])
                command.ui_answer_event.set()

            elif text[0] == "/":
                # Occurs when the ui process has exited
                ut = simple_thread(tidyquit)

            elif text[0] == "_":
                # Initiated by 'tidyquit()' to quit the thread and thus
                # also the main process.
                command.send("/")
                return

            else:
                command.fatal(_("Unexpected message from ui"), text)

        elif source == "X":
            if text[0] == "@":
                if command.ready.is_set():
                    command.fatal(_("Unexpected end of 'supershell' process."))
                command.ok = (text[1] == "0")
                command.ready.set()
            elif text[0] == "-":
                command.result.append(text[1:])

            command.log(line.strip())

        else:
            command.fatal(_("Main process received illegal command"), line)

#---------------------------


def simple_thread(func, *args):
        t = threading.Thread(target=func, args=args)
        t.start()


def gtstart(process):
    """A thread function for reading input from the ui subprocess line
    by line. The lines are placed in the communication queue.
    """
    while True:
        line = process.stdout.readline()
        if not line:
            break
        # Pass on the output of the process
        commqueue.put("G:%s" % line)

    process.wait()
    commqueue.put("G:/%d\n" % process.returncode)


def itstart():
    """A thread function for reading input from stdin line
    by line. The lines are placed in the communication queue.
    """
    while True:
        line = sys.stdin.readline()
        # Pass on the output of the process
        commqueue.put("X:%s" % line)


re_progress = re.compile(r"X:-\[.*\](.* ([0-9]+)%)")
def ltstart():
    """A thread function for reading log lines from the log queue and
    passing them to the logger.
    """
    progress = ""
    while True:
        line = logqueue.get()
        # Filter the output of mksquashfs
        m = re_progress.match(line)
        if m:
            if not progress:
                command.ui("log:logtext.append_and_scroll", "dummy\n")
            percent = m.group(2)
            if progress == percent:
                continue
            else:
                progress = percent
                command.ui("log:logtext.undo")
                line = "X:++++%s\n" % m.group(1)
        else:
            progress = ""
        command.ui("log:logtext.append_and_scroll", line)


def tidyquit():
    command.unmount()
    commqueue.put("G:_\n")


if __name__ == "__main__":
    commqueue = Queue()
    logqueue = Queue()
    # Various ui toolkits could be supported, but at the moment there
    # is only ...
    if True:
        # In list form suitable for subprocess.Popen()
        guiexec = ["%s/modules/guibuild.py" % base_dir]
    guiprocess = Popen(guiexec, cwd=base_dir, stdin=PIPE, stdout=PIPE)
    gthread = simple_thread(gtstart, guiprocess)

    __builtin__.command = Command()
    __builtin__.config = base.LarchConfig(os.environ["HOME"])

    lthread = simple_thread(ltstart)

    ithread = simple_thread(itstart)

    __builtin__.supershell = command.supershell
    command.run()
    mainloop(sys.stdin)

