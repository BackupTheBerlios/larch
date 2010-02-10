#!/usr/bin/env python
#
# installer.py - format partitions and install system
#
# (c) Copyright 2010 Michael Towers (larch42 at googlemail dot com)
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
# 2010.02.10

import threading

import backend, fstab


class Installer:
    """This class manages the copying of the live system to the disk.
    It also handles the peripheral requirements of partition formatting
    and mounting, and the generation of an initramfs and initial /etc/fstab
    (the latter by means of the fstab module).
    """
    def __init__(self, out_mb=False, out_percent=False, dbg_flags=""):
        self.dbg_flags = dbg_flags
        self.out_mb = out_mb
        self.out_percent = out_percent

    def count_files(self):
        rc, op = scripts.script("count-files")
        if rc == 0:
            self.nfiles = int(op.strip())


    def run(self, partlist=[]):
        self.nfiles = 0
        if self.out_percent:
            t = threading.Thread(target=self.count_files, args=())
            t.start()

        self.partlist = backend.Partlist(partlist)

        # Format
#debugging
        if "f" not in self.dbg_flags:
#-

# Maybe not formatting should be a genuine option? One might have done it
# already ...

            if not self.format():
                return 1


        # Mount
        if not mounting.mount():
            return 2


        # Copy system
#debugging
        if "i" not in self.dbg_flags:
#-
            if not self.copysystem():
                errout( _("Copying of system data failed"))
                return 3
            io.out("#>" + _("Copy finished:") + "%6.1f GB" %
                    (float(self.installed) / 10**9))
            if self.nfiles:
                io.out(":p>")         # Clear percent progress

            io.out("#>" + _("Initial tweaks to installed system"))
            if not scripts.run("fix-system1", mounting.mount_point()):
                errout(_("Initial installed-system tweaks failed"))
                return 4

            # Delivify (including running 'larch0' script)
            io.out("#>" + _("Removing live-system modifications"))
            if not scripts.run("fix-system2", mounting.mount_point()):
                errout(_("Failure while removing live-system modifications"))
                return 5

            # initramfs
            io.out("#>" + _("Generating initramfs"))
            if not mounting.run_mount_devprocsys("do-mkinitcpio",
                    mounting.mount_point()):
                errout(_("Problem building initramfs"))
                return 6

        # The partition(s) must be unmounted before autogenerating /etc/fstab
        if not mounting.unmount():
            return 7

        # /etc/fstab
        io.out("#>" + _("Generating /etc/fstab"))
        return fstab.generate(self.partlist)


    def format(self):
        for part in self.partlist.get_all():
            dev = part[1]
            fmt = part[2]
            if fmt:
                io.out("#>" + _("Formatting %s") % dev)
                if not scripts.run("part-format", dev, fmt):
                    errout("!>" + _("Formatting of %s failed") % dev)
                    return False
        return True


    def copysystem(self):
        io.out("#>" + _("Copying system to selected partition(s)"))
        rootdir = ""
        self.installed = 0      # bytes
        mbi = 0                 # MB
        files = 0
        percent = 0
        fail = 0

        p = scripts.start_script("copy-system", mounting.mount_point())
        while True:
            line = p.stdout.readline()
            if not line:
                break

            if "!" not in line:
                if fail < 4:
                    fail += 1
                    debug("copy-system -> " + line)
                continue
            fname, size = line.split("!")
            frdir = fname.lstrip("/").split("/", 1)[0]
            if frdir != rootdir:
                rootdir = frdir
                io.out("#>" + " ... /%s ..." % frdir)
            self.installed += int(size)
            files += 1
            mb = (self.installed + 5*10**5) / 10**6
            if (self.out_mb > 0) and ((mb - mbi) >= self.out_mb):
                io.out(":m>%d" % mb)
                mbi = mb
            if self.nfiles:
                pc = files * 100 / self.nfiles
                if (pc > percent) and pc <= 100:
                    io.out(":p>%d" % pc)
                    percent = pc

        # The process has ended.
        return scripts.end_script(p)



if __name__ == "__main__":
    import os, sys, traceback, console
    backend.start_translator()

    from optparse import OptionParser, OptionGroup
    parser = OptionParser(usage=_("usage: %prog [options]"))
    parser.add_option("-m", "--sizemb", action="store", dest="mb",
            type="int", default=0,
            help=_("Output installed MB (progress) with step of this size"))
    parser.add_option("-p", "--progress", action="store_true", dest="progress",
            default=False, help=_("Output estimated progress as percent"))
    parser.add_option("-d", "--debug", action="store", type="string",
            default="", dest="dbg", help=_("Debug flags %s") % "[fi]",
            metavar="FLAGS")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
            default=False, help=_("Suppress output messages, except errors"))
    group = OptionGroup(parser, _("Passing installation partitions"),
            _("   mount-point:device:format:uuid/label ..."
            " More than one such descriptor can be passed, using ',' as"
            " separator.   The first entry should be for root"
            " (mount-point is '/'), swap partitions have mount-point 'swap'."
            "   format should be 'ext4' or 'jfs', for example. If it is"
            " empty, no formatting will be performed. Also swap"
            " partitions should have this field empty.   The final entry"
            " may be empty (implying the system default will be used),"
            " otherwise:   "
            "   -: using straight device names (/dev/sdXN),"
            "   LABEL=xxxxx: using partition labels,"
            "   UUID=xxxxx: using UUIDs"))
    group.add_option("-l", "--partitions", action="store", type="string",
            default="", dest="parts", help=_("Pass partition list"),
            metavar="PARTLIST")
    parser.add_option_group(group)
    (options, args) = parser.parse_args()

    backend.init(console.Console(options.quiet))

    installer = Installer(options.mb, options.progress, dbg_flags = options.dbg)

    sys_quit(installer.run(options.parts.split(',')))
