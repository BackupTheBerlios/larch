#!/usr/bin/env python
#
# console.py
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
# 2009.09.02

"""Implement a command line driven user interface for larch.
"""

import sys, os
import json
import threading
from Queue import Queue


def out(line):
    sys.stdout.write(line)
    sys.stdout.flush()


class Ui:
    def __init__(self, commqueue, flag, guiexec):
        self.queue = commqueue
        self.flag = flag
        self.autocontinue = False

        # The (console) input handling
        self.inqueue = Queue()
        self.ithread = threading.Thread(target=self.inputthread_start)
        self.ithread.start()

        # A thread for running the commands
        self.guiprocess = None
        self.gthread = threading.Thread(target=self.commandthread_start,
                args=(sys.argv[1:],))
        self.gthread.start()


# Input handling .................
    def inputthread_start(self):
        """A thread function for reading input from stdin line by line.
        The lines are placed in a queue.
        """
        while True:
            line = sys.stdin.readline()
            self.inqueue.put(line)

    def inflush(self):
        r = ""
        try:
            while True:
                r += self.inqueue.get_nowait()
        except:
            return r

    def ingetline(self, prompt=None):
        if prompt != None:
            out(prompt)
        self.inqueue.get()

# End of the input handling .................


    def commandthread_start(self, arglist):
        """A thread function for reading commands from a command list.
        The commands are passed to the 'do' method.
        """
        cmd = []
        lines = []
        if arglist[0] == "-f":
            # Get commands from file
            if len(arglist) > 2:
                errout(_("WARNING: Superfluous arguments ignored -\n"))
                errout(" ... " + " ".join(arglist[2:]))
            fh = open(arglist[1])
            for line in fh:
                line = line.strip()
                if line.startswith("#"):
                    continue
                lines.append(line)
            fh.close()

        else:
            # Get commands from command line
            lines = arglist[1:]

        for cmd in lines:
            r = self.do(cmd):
            if r != 0:
                break
        self.queue.put("%s/%d\n" % (self.flag, r))


    def infoDialog(self, message, title=None):
        if title == None:
            title = _("Information")
        out("***** %s *****\n" % title)
        out(message + "\n")
        if self.autocontinue:
            return True
        else:
            self.ingetline(_("Press <Enter> to continue"))
            return True


    def confirmDialog(self, message, title=None):
        if title == None:
            title = _("Confirmation")
        out("***** %s *****\n" % title)
        out(message + "\n")
        if self.autocontinue:
            return True
        else:
            l = self.ingetline("%s (y) | %s (n) ? " % (_("Yes"), _("No")))
            return (l.strip()[0] in "yY")


    def error(self, message, title=None, fatal=True):
        """In console mode all errors are fatal.
        """
        if title == None:
            title =  _("ERROR")
        self.infoDialog(message, title)
        command.uiquit()
        assert False


    def sendsig(self, sig, *args):
        self.queue.put("%s^%s %s" % (self.flag, self.name, json.dumps([None, args])))


    def respond(self, result):
        self.queue.put("%s@%s\n" % (self.flag, json.dumps(result)))





????
    def command(self, cmd, *args):
        pass

    def ask(self, cmd, *args):
        pass




set_platform (at most 32/64, and only on 64)
set_bootloader
set_medium_detection

set_bootlarch (* binary)
set_partition_format (* binary)
set_use_build_mirror (* binary)
set_use_project_mirrorlist (* binary)

# Then there are the places where a name, a path or other line of text
# needs to be supplied.
set_ipath
set_buildmirror
set_pacman_cache
set_label
pacman_sy
pacman_s
pacman_u
pacman_r

# Actions
install
larchify (+ sshkeys + oldsquash)
create_iso
write_partition (+ partition)
create_bootiso

show_partitions

# How to set ui.autocontinue?
# What about using old system.sqf and ssh-keys? These are not in the project memory.

def infoline(item, value):
    out("  %-25s %s\n" % (item, value))

def show_project_info():
    yes = _("Yes")
    no = _("No")
    infoline(_("Project Name:"), config.project)
    infoline(_("Profile:"), config.get("profile"))
    infoline(_("Installation Path:"), config.get("install_path"))
    infoline(_("Working Directory:"), config.working_dir)
    infoline(_("Platform:"), config.get("platform"))
    infoline(_("Installation Mirror:"), config.get("localmirror"))
    infoline(_("--- use mirror:"), yes if config.get("uselocalmirror") else no)
    infoline(_("Use Project Mirrorlist:"), yes if config.get("usemirrorlist") else no)
    infoline(_("Bootloader:"), config.get("medium_btldr"))
    infoline(_("Medium Detection:"), config.get("medium_search"))
    infoline(_("Medium Label:"), config.get("medium_label"))
    infoline(_("Package Cache:"), config.get("pacman_cache"))

def show_projects():
    out(_("Projects:\n"))
    for p in config.getsections():
        out("    %s\n" % p)

def show_profiles():
    out(_("Profiles (in %s):\n") % config.profile_dir)
    for p in config.profiles():
        out("    %s\n" % p)

def show_example_profiles():
    out(_("Example Profiles (in %s):\n") % base_dir + "/profiles")
    for p in os.listdir(base_dir + "/profiles"):
        out("    %s\n" % p)






def set_project(name):
    try:
        i = config.getsections().index(name)
        ui.sendsig(":choose_project_combo*changed", i)
    except:
        error(_("Unknown project name: '%s'") % name)

def new_project(name):
    ui.sendsig("$*new_project_name*$", name)

def del_project(name):
    if name in config.getsections():
        ui.sendsig(":project_delete*clicked", name)
    else:
        error(_("Unknown project name: '%s'") % name)


def set_profile(name):
    try:
        i = config.profiles().index(name)
        ui.sendsig(":choose_profile_combo*changed", i)
    except:
        error(_("Unknown profile name: '%s'") % name)

def rename_profile(name):
    ui.sendsig("$*rename_profile*$", name)

def new_profile(path, name=None):
    ui.sendsig("$*make_new_profile*$", path, name)

def del_profile(name):
    if name in config.profiles():
        ui.sendsig(":profile_delete*clicked", name)
    else:
        error(_("Unknown profile name: '%s'") % name)




class Logger:
    def __init__(self):
        self._openfile()
        self.visible = True
        self.buffered = None

    def _openfile(self):
        self.logfile = open(config.working_dir + "/larch.log", "w")

    def setVisible(self, on):
        self.visible = on

    def clear(self):
        self.logfile.close()
        self._openfile()
        if self.visible:
            sys.stdout.write("**** CLEAR LOG ****\n")
            sys.stdout.flush()

    def addLine(self, line):
        if self.buffered != None:
            self.logfile.write(self.buffered)
            if self.visible:
                sys.stdout.write("\n")
        self.buffered = line
        if self.visible:
            sys.stdout.write("LOG: " + line.rstrip())
            sys.stdout.flush()

    def undo(self):
        self.buffered = None
        if self.visible:
            sys.stdout.write("\r" + " "*120 + "\r")
            sys.stdout.flush()

    def quit(self):
        self.logfile.close()
        if self.visible:
            sys.stdout.write("\n**** Done ****\n")
            sys.stdout.flush()

