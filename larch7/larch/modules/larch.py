#!/usr/bin/env python
#
# larch.py
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
# 2009.09.08


"""
This is the main module of the larch program, which should be started with
root priveleges. If it is started as a normal user, the actual building
commands will not be exectued, but it might still be useful for debugging.

The actual building instructions are run from a separate process - the
backend - which runs shell commands on demand from this main process.
Communication between the two processes is via pipes to the backend's
stdio channels.

As soon as the backend has been started, the main process drops its
privileges and continues running as the logged in user. Thus it is
possible to change the configuration files within larch and preserve the
correct ownership.

The graphical user interface is also run as a separate process and the
communication also runs via pipes to the subprocess's stdio channels.
Data is passed as json objects.

The command-line user interface runs in the same process but a separate
thread is used to dispatch the commands - several commands can be passed
on the command line. The dispatcher waits for one command to complete
before sending the next, so the behaviour should be 'as expected'.

A thread is used to read input from the root process and another
thread is used to read input from the user interface. Both these threads
place the lines they receive in a queue which is read by the main thread.
The received lines are then acted upon.

The main work of the program (the steering of the live system
construction) is handled by the imported modules and run in a separate
thread.
"""

import os, sys, traceback, re, pwd, signal

import __builtin__
__builtin__.base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append("%s/modules" % base_dir)
script_dir = "%s/buildscripts" % base_dir

from subprocess import Popen, PIPE, STDOUT
import threading, traceback
from Queue import Queue
import json

import base
import logging
from installation import Installation

from projectpage import ProjectPage
from installpage import InstallPage
from buildpage import BuildPage
from mediumpage import MediumPage
from tweakpage import TweakPage


def errout(text, quit=0):
    sys.stderr.write(text)
    sys.stderr.flush()
    if quit:
        sys.exit(quit)
__builtin__.errout = errout

def debug(text):
    errout("DEBUG: " + text.strip() + "\n")
__builtin__.debug = debug


import gettext
lang = os.getenv("LANG")
if lang:
    gettext.install('larch', base_dir+'/i18n', unicode=1)


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


class Command:
    def __init__(self, tosuper):
        """The user interface must already be running before entering here.
        """
        self.ostream = tosuper
        self.ready = threading.Event()
        self.ready.set()

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
        self.pages = [ProjectPage(), InstallPage(), BuildPage(),
                MediumPage(), TweakPage()]

        # Connect up the signals and slots
        self.connections = {
                "$$$uiquit$$$": [self.uiquit],
                "$$$hidelog$$$": [self._activatehidelog],
                "$showlog*toggled$": [self._showlog],
                ":notebook*changed": [self.pageswitch],
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
        ui.go()


    def pageswitch(self, index):
        self.pages[index].setup()


    def log(self, line):
        # The line should not have a newline terminator
        logqueue.put(line)


    def send(self, line):
        self.log(line)
        if superprocess:
#TODO: Does this need a lock?
            self.ostream.write("%s\n" % line)
            self.ostream.flush()
        else:
            if line.startswith("/"):
                commqueue.put("X:/0 ...DUMMY SUPERSHELL QUITTING...\n")
            else:
                commqueue.put("X:@0 ...DUMMY SUPERSHELL...\n")


    def worker(self, *args):
        self.blocking = True
        self.pthread = threading.Thread(target=self.worker_run, args=args)
        self.pthread.start()


    def worker_run(self, slots, *args):
        ui.command(":larch.busy", ":notebook", True)
        try:
            for s in slots:
                s(*args)
        except:
            if self.breakin == 0:
                typ, val, tb = sys.exc_info()
                fatal_error("".join(traceback.format_exception(typ, val, tb)))

        self.blocking = False
        ui.completed(self.breakin == 0)


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
        ui.command(":showlog.set", False)


    def _showlog(self, on):
        # This is not called from the worker thread, but I think it's ok
        logger.setVisible(on)


    def _clearlog(self):
        # This is not called from the worker thread, but I think it's ok
        logger.clear()


    def sigint(self, num, frame):
        """CONSOLE MODE ONLY: A handler for SIGINT. Tidy up properly and quit.
        First kill potential running supershell process, then terminate
        logger, and then, finally, terminate the ui process.
        """
        self.uiquit()

    def uiquit(self):
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

        # Tell the logger to quit
        logqueue.put("L:/\n")

        # Wait until logger process has terminated
        lthread.join()

        # Tell the user interface to exit, which will in turn cause the
        # thread reading its output to terminate (see function 'gtstart').
        ui.sendui("/")


    def mount(self, src, dst, opts=""):
        if supershell("mount %s %s %s" % (opts, src, dst)).ok:
            self.mounts.append(dst)
            return True
        return False


    def unmount(self, dst=None):
        if dst == None:
            mounts = list(self.mounts)
        elif type(dst) in (list, tuple):
            mounts = list(dst)
        else:
            mounts = [dst]

        r = True
        for m in mounts:
            if supershell("umount %s" % m).ok:
                self.mounts.remove(m)
            else:
                r = False
        return r


    def edit(self, fname, source=None, label=None, filter=None):
        if fname[0] == "/":
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
        ui.command("editor:label.set", label)
        ui.command("editor:text.set", readfile(f) if os.path.isfile(f)
                else source)
        if ui.ask("editor:editor.showmodal"):
            t = ui.ask("editor:text.get").encode("utf8")
            if t[-1] != "\n":
                t += "\n"
            d = os.path.dirname(f)
            if not os.path.isdir(d):
                os.makedirs(d)
            savefile(f, t)


    def browser(self, path):
        cmd = config.get("filebrowser").replace("%", path)
        Popen(cmd + " &", shell=True)


    def chroot(self, cmd, mounts=[]):
        ip = config.get("install_path")
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


    def script(self, cmd):
        s = supershell("%s/%s" % (script_dir, cmd))
        if s.ok:
            return ""
        else:
            return "SCRIPT ERROR: (%s)\n" % cmd + "".join(s.result)


    def check_platform(self, report=True):
        arch = Popen(["cat", config.ipath(".ARCH")],
                stdout=PIPE, stderr=PIPE).communicate()[0].strip()
        if arch:
            if arch != config.get("platform"):
                if report:
                    config_error(_("Platform error, installed system is %s")
                            % arch)
                return False
        else:
            if report:
                config_error(_("No installed system found"))
            return False
        return True


    def enable_tweaks(self):
        ui.command(":notebook.enableTab", 4, (config.get("install_path") != "/"
                and self.check_platform(report=False)))


    def get_partitions(self):
        """Get a list of available partitions (only unmounted ones
        are included).
        """
        # First get a list of mounted devices
        mounteds = []
        fh = open("/etc/mtab")
        for l in fh:
            dev = l.split()[0]
            if dev.startswith("/dev/sd"):
                mounteds.append(dev)
        fh.close()
        # Get a list of partitions
        partlist = []
        for line in supershell("sfdisk -uM -l").result:
            if line.startswith("/dev/sd"):
                fields = line.replace("*", "").replace(" - ", " ? ")
                fields = fields.replace("+", "").replace("-", "").split()
                #debug("F5 '%s'" % fields[5])
                if fields[5] in ["0", "5", "82"]:
                    #debug("No")
                    continue        # ignore uninteresting partitions
                if fields[0] in mounteds:
                    continue        # ignore mounted patitions
                # Keep a tuple (partition, size in MiB)
                partlist.append("%-12s %12s MiB" % (fields[0], fields[3]))
        return partlist


    def NYI(self):
        ui.ask("infoDialog", _("Function not yet implemented"))


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
    ui.error(text, _("CONFIG ERROR"))
__builtin__.config_error = config_error

def run_error(text):
    ui.error(text, _("BUILD ERROR"))
__builtin__.run_error = run_error

def fatal_error(text):
    ui.error(text, fatal=True)
__builtin__.fatal_error = fatal_error

#---------------------------
# Catch all unhandled errors.
def errorTrap(type, value, tb):
    etext = "".join(traceback.format_exception(type, value, tb))
    ui.error(etext, _("This error could not be handled"), fatal=True)

sys.excepthook = errorTrap
#---------------------------


#+++++++++++++++++++++++++++
def mainloop():
    """Loop to read input and act on it.
    """
    global exitcode
    while True:
        # We may have to wait for a worker thread to finish, hence the
        # following repeated test for the end of a thread after a breakin.
        line = commqueue.get()
        source, text = line.split(":", 1)
        if source == "G":
            if text[0] == "^":
                # signal, call slots
                sig, args = text[1:].split(None, 1)
                arglst = json.loads(args)
                slots = command.connections.get(sig)
                if slots:
                    if ":&" in ":" + sig:
                        # Such slots must be run by a background thread
                        # Only one at a time is permitted
                        if command.blocking:
                            run_error(_("Received unexpected signal: '%s'")
                                    % line.strip())
                        else:
                            command.worker(slots, *arglst[1])
                    else:
                        # Normal slots are run directly - they must be quick
                        for s in slots:
                            s(*arglst[1])

            elif text[0] == "@":
                # The response to an enquiry
                if ui.answer_event.is_set():
                    fatal_error(_("Unexpected response from ui:\n") + text)
                ui.answer = json.loads(text[1:])
                ui.answer_event.set()

            elif text[0] == "/":
                # Occurs when the ui process has exited
                ut = simple_thread(tidyquit)
                exitcode = int(text[1:])

            elif text[0] == "_":
                # Initiated by 'tidyquit()', we should be ready to quit.
                # First shut down the backend process (superprocess)
                command.send("/")

            else:
                fatal_error(_("Unexpected message from ui:\n") + text)

        elif source == "X":
            if text[0] == "@":
                if command.ready.is_set():
                    fatal_error(_("Unexpected end of 'supershell' process."))
                command.ok = (text[1] == "0")
                command.ready.set()
            elif text[0] == "-":
                command.result.append(text[1:])
            elif text[0] == "/":
                # Occurs when the backend process has exited
                #try:
                #    while True:
                #        # To unblock threads waiting for the queue
                #        commqueue.task_done()
                # except:
                #    pass
                return

            command.log(line.strip())

        else:
            fatal_error(_("Main process received illegal message:\n") + line)

        commqueue.task_done()

#---------------------------


def simple_thread(func, *args):
        t = threading.Thread(target=func, args=args)
        t.start()
        return t


def substart(process, flag):
    """A thread function for reading input from a subprocess line
    by line. The lines are placed in the communication queue.
    """
    while True:
        line = process.stdout.readline()
        if not line:
            break
        # Pass on the output of the process
        commqueue.put(flag + line)

    process.wait()
    commqueue.put("%s/%d\n" % (flag, process.returncode))


re_mksquashfs = re.compile(r"X:-\[.*\](.* ([0-9]+)%)")
re_pacman = re.compile(r"X:-.*\[([-#]+)\]\s+[0-9]+%")
def ltstart():
    """A thread function for reading log lines from the log queue and
    passing them to the logger.
    """
    progress = ""
    while True:
        line = logqueue.get()
        if line.startswith("L:/"):
            # Quit logging
            logger.quit()
            break
        # Filter the output of mksquashfs
        m = re_mksquashfs.match(line)
        if m:
            if not progress:
                logger.addLine("dummy\n")
            percent = m.group(2)
            if progress == percent:
                continue
            else:
                progress = percent
                logger.undo()
                line = "X:++++%s\n" % m.group(1)
        else:
            m = re_pacman.match(line)
            if m:
                if '#' in m.group(1):
                    logger.undo()

            progress = ""
        logger.addLine(line)


def tidyquit():
    command.unmount()
    commqueue.put("G:_\n")


if __name__ == "__main__":

    if os.getuid() == 0:
        # Start backend process (supershell)
        superprocess = Popen([base_dir + "/modules/backend.py"],
                stdin=PIPE, stdout=PIPE)

    else:
        errout(_("You need to run larch as root!\n  - otherwise"
                " the build instructions cannot be carried out.\n"))
        # Use a dummy supershell
        superprocess = None

    # Drop root privileges
    chid()

    commqueue = Queue()
    logqueue = Queue()

    # Various ui toolkits could be supported, but at the moment there
    # is only support for pyqt (apart from the console)
    if (len(sys.argv) > 1) and (sys.argv[1].startswith("-c")):
        from console import Ui, Logger
        guiexec = None
    else:
        from gui import Ui, Logger
        if (len(sys.argv) == 1) or (sys.argv[1] == "-pyqt"):
            guiexec = [base_dir + "/modules/pyqt/larchgui.py"]
        else:
            errout(_("ERROR: Unsupported option - '%s'\n") % sys.argv[1])
            sys.exit(1)

    __builtin__.ui = Ui(commqueue, "G:", guiexec)
    __builtin__.logger = Logger()

    __builtin__.installation = Installation()

    __builtin__.command = Command(superprocess.stdin if superprocess else None)
    __builtin__.config = base.LarchConfig(os.environ["HOME"])

    # Start log reader thread
    lthread = simple_thread(ltstart)

    # Start thread to read from backend
    if superprocess:
        xthread = simple_thread(substart, superprocess, "X:")

    __builtin__.supershell = command.supershell

    signal.signal(signal.SIGINT, command.sigint)

    command.run()
    mainloop()

    sys.exit(exitcode)
