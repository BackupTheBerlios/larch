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
# 2009.09.08


# This is actually pretty f.u. - the whole signal / threading bit doesn't seem
# to be functional, it is too complicated, and untidy.


"""Implement a command line driven user interface for larch.
"""

import sys, os, traceback
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
        self.autocontinue = ("x" in sys.argv[1])

        # Associate command names with functions (aliases are allowed)
        self.functions = {}
        for assoc in function_list:
            for n in assoc[1:]:
                self.functions[n] = assoc[0]


    def go(self):
        logger.init()
        logger.setVisible("l" not in sys.argv[1])

        self.block = threading.Event()
        self.gthread = threading.Thread(target=self.t_run, args=sys.argv[2:])
        self.gthread.start()


    def t_run(self, *arglist):
        try:
            for cmd in arglist:
                self.queue.join()
                r = self.do(cmd)
                if r != 0:
                    break
        except:
            r = 1
        self.sendsig("$$$uiquit$$$")
        self.queue.put("%s/%d\n" % (self.flag, r))
        return


    def sendsigB(self, sig, *args):
        self.block.clear()
        self.sendsig(sig, *args)
        self.block.wait()


    def infoDialog(self, message, title=None):
        if title == None:
            title = _("Information")
        out("***** %s *****\n" % title)
        out(message + "\n")
        if self.autocontinue:
            return True
        else:
            raw_input(_("Press <Enter> to continue"))
            return True


    def confirmDialog(self, message, title=None):
        if title == None:
            title = _("Confirmation")
        out("***** %s *****\n" % title)
        out(message + "\n")
        if self.autocontinue:
            return True
        else:
            l = raw_input("%s (y) | %s (n) ? " % (_("Yes"), _("No")))
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
        self.queue.put("%s^%s %s" % (self.flag, sig, json.dumps([None, args])))


    def respond(self, result):
        self.queue.put("%s@%s\n" % (self.flag, json.dumps(result)))


    def do(self, cmdline):
        cmda = cmdline.split()
        fn = self.functions.get(cmda[0])
        if fn:
            fn(*cmda[1:])
            return 0
        else:
            self.error(_("Unknown command: %s") % cmda[0])


    # The gui interface functions are not used here
    def command(self, cmd, *args):
        return

    def ask(self, cmd, *args):
        return None

    def sendui(self, line):
        return

    def completed(self):
        self.block.set()


#-----------------------------------------------------------
# Main Actions

def x_install():
    ui.sendsigB(":&install*clicked")

def x_larchify(opts=""):
    """opts: string containing 's' to generate sshkeys, 'r' to use oldsquash
    """
    ui.sendsigB("&larchify&", "s" in opts, "r" in opts)

def x_create_iso():
    """Create an iso of the live system
    """
    ui.sendsigB("&makelive&", True, "", False, True)
    # + iso? + partition + format? + larchboot?

def x_write_partition(part, opts=""):
    """Write the live system to the given partition.
    opts: string containing 'n' to suppress formatting, 'l' to force larchboot
    """
    ui.sendsigB("&makelive&", False, part, 'n' not in opts, 'l' in opts)
    # + iso? + partition + format? + larchboot?

def x_create_bootiso(part):
    ui.sendsigB("&bootiso&", part)
#-----------------------------------------------------------


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

def show_partitions():
    out(_("Available Partitions:\n"))
    for p in command.get_partitions():
        out(p + "\n")


def set_project(name):
    try:
        i = config.getsections().index(name)
        ui.sendsig(":choose_project_combo*changed", i)
    except:
        ui.error(_("Unknown project name: '%s'") % name)

def new_project(name):
    ui.sendsig("$*new_project_name*$", name)

def del_project(name):
    if name in config.getsections():
        ui.sendsig(":project_delete*clicked", name)
    else:
        ui.error(_("Unknown project name: '%s'") % name)


def set_profile(name):
    try:
        i = config.profiles().index(name)
        ui.sendsig(":choose_profile_combo*changed", i)
    except:
        ui.error(_("Unknown profile name: '%s'") % name)

def rename_profile(name):
    ui.sendsig("$*rename_profile*$", name)

def new_profile(path, name=None):
    ui.sendsig("$*make_new_profile*$", path, name)

def del_profile(name):
    if name in config.profiles():
        ui.sendsig(":profile_delete*clicked", name)
    else:
        ui.error(_("Unknown profile name: '%s'") % name)


def set_ipath(path):
    ui.sendsig("$*set_ipath*$", path)


def set_platform(arch):
    try:
        i = config.platforms.index(arch)
        ui.sendsig(":platform*changed", i)
    except:
        ui.error(_("Available platforms: %s") % repr(config.platforms))


def set_buildmirror(path):
    ui.sendsig("$*set_build_mirror*$", path)


def set_pacman_cache(path):
    ui.sendsig("$*set_pacman_cache*$", path)


def use_build_mirror(on):
    ui.sendsig(":use_local_mirror*toggled", on[0] in "yY")


def use_project_mirrorlist(on):
    ui.sendsig(":mirrorlist*toggled", on[0] in "yY")


def set_bootloader(bl):
    bl = bl.lower()
    if bl == "isolinux":
        bl = "syslinux"
    elif bl in ("grub", "syslinux", "none"):
        ui.sendsig(":$%s*toggled" % bl, True)
    else:
        ui.error(_("Invalid bootloader: %s") % bl)


def set_medium_detection(mdet):
    mdet = mdet.lower()
    if mdet in ("search", "uuid", "label", "device"):
        ui.sendsig(":$%s*toggled" % mdet, True)


def set_label(label):
    ui.sendsig("$*new_label*$", label)


def pacman_s(*args):
    ui.sendsig("$*pacmanS*$", " ".join(args))


def pacman_r(*args):
    ui.sendsig("$*pacmanR*$", " ".join(args))


def pacman_u(filepath):
    ui.sendsig("$*pacmanU*$", filepath)


def pacman_sy(filepath):
    ui.sendsig(":sync*clicked")


function_list = (
    [x_install, "install", "i"],
    [x_larchify, "larchify", "l"],
    [x_create_iso, "create_iso", "ci"],
    [x_write_partition, "create_part", "cp"],
    [x_create_bootiso, "create_bootiso", "cb"],
    [show_project_info, "show_project_info", "i?"],
    [show_projects, "show_projects", "P?"],
    [show_profiles, "show_profiles", "p?"],
    [show_example_profiles, "show_example_profiles", "e?"],
    [show_partitions, "show_partitions", "d?"],
    [set_project, "set_project", "P:"],
    [new_project, "new_project", "P+"],
    [del_project, "del_project", "P-"],
    [set_profile, "set_profile", "p:"],
    [rename_profile, "rename_profile", "p!"],
    [new_profile, "new_profile", "p+"],
    [del_profile, "del_profile", "p-"],
    [set_ipath, "set_ipath", "ip:"],
    [set_platform, "set_platform", "arch:"],
    [set_buildmirror, "set_buildmirror", "m:"],
    [set_pacman_cache, "set_pacman_cache", "cache:"],
    [use_build_mirror, "use_build_mirror", "um:"],
    [use_project_mirrorlist, "use_project_mirrorlist", "upm:"],
    [set_bootloader, "set_bootloader", "bl:"],
    [set_medium_detection, "set_medium_detection", "md:"],
    [set_label, "set_label", "lab:"],
    [pacman_s, "pacman_s", "ps:"],
    [pacman_r, "pacman_r", "pr:"],
    [pacman_u, "pacman_u", "pu:"],
    [pacman_sy, "pacman_sy", "psy"],
)


class Logger:
    def __init__(self):
        self.visible = True
        self.buffered = None

    def init(self):
        self._openfile()

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
            self.logfile.write(self.buffered + "\n")
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
        if self.buffered != None:
            self.logfile.write(self.buffered)
        self.logfile.close()
        if self.visible:
            sys.stdout.write("\n**** Done ****\n")
            sys.stdout.flush()

