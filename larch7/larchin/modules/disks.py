# disks.py - discover possible (disk-like) installation devices
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
# 2009.10.13

from backend import DiskInfo
import re

doc = _("""
<h2>Disk Selection</h2>
<p>On the basis of the detected disk(-like) devices a choice of devices
for automatic or manual partitioning will be offered.
</p>
<p>Only devices with no mounted partitions and of sufficient size can be
partitioned automatically, these are marked with '+' in the first column.
Any others will be listed with '-' in the first column. They may be
partitioned manually, but great care must be exercised when partitioning
devices which are (partially) in use, and installation to a device which
is actually too small will prove to be difficult, though the manual
option is more flexible than the automatic one.
</p>
<p>The automatically calculated partitioning scheme allows only a limited
amount of tweaking, so if you want more control over the partitioning of
your disk drives and the location of the installation, you will need to
select manual partitioning. This will normally allow the use of the
external tools cfdisk and gparted or kde's partition-manager.
</p>
<p>In the case of manual partitioning the selection of the mount points
is done separately in the 'Select Installation Partitions' stage, which
will be skipped if the automatic partitioning scheme is accepted.
</p>
<p>Selecting one of the devices offered for automatic partitioning will
not immediately cause it to be modified, so try it out without fear. You
can return here and choose manual partitioning later if necessary.
</p>""")


class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&device-select&", self.select_page),
                ("disks:device-list*select", self.select_device),
                ("disks:auto*toggled", self.auto_toggle),
                ("disks:guipart*toggled", self.guipart_toggle),
                ("disks:cfdisk*toggled", self.cfdisk_toggle),
                ("disks:nopart*toggled", self.nopart_toggle),
                ("disks:keep1*toggled", self.keep1_toggle),
            ]

    def select_page(self):
        command.pageswitch(self.page_index,
                _("Disk information and selection"))

    def __init__(self, index):
        self.page_index = index
        self.device_index = 0
        ui.newwidget("List", "^disks:device-list", selectionmode="Single",
                tt=_("Select the device to inspect, or for partitioning"))
        ui.newwidget("List", "disks:device-partitions", selectionmode="None",
                tt=_("The partitions on the selected device"))

        ui.newwidget("Button", "^disks:ntfs-shrink",
                text=_("Shrink first partition (Windows - NTFS)"))
        ui.newwidget("CheckBox", "^disks:keep1",
                text=_("Keep first partition (Windows - NTFS)"))

        ui.newwidget("Frame", "disks:choose_partition_method",
                text=_("Choose Partitioning Method"))
        ui.newwidget("RadioButton", "^disks:auto",
                text=_("Autopartition and install to selected device"))
        ui.newwidget("RadioButton", "^disks:guipart",
                text=_("Graphical partition manager"))
        ui.newwidget("RadioButton", "^disks:cfdisk",
                text=_("Console partition manager (cfdisk) on selected device"))
        ui.newwidget("RadioButton", "^disks:nopart",
                text=_("Use existing partitions"))

        ui.layout("disks:choose_partition_method", ["*HBOX*",
                ["*VBOX*", "disks:auto", "disks:guipart",
                        "disks:cfdisk", "disks:nopart"],
                ["*SPACE", 50],
                ["*VBOX*", "disks:keep1", "disks:ntfs-shrink", "*SPACE"]])
        ui.layout("page:disks", ["*VBOX*",
                ["*HBOX*", "disks:device-list", "disks:device-partitions"],
                "*SPACE", "disks:choose_partition_method"])

        ui.command("disks:device-list.setHeaders", ["", _("Device"),
                _("Size"), _("Model")])
        ui.command("disks:device-partitions.setHeaders", [_("Partition"),
                _("Size (GB)"), _("Type")])
        self.method = ""

    def setup(self):
        # Test for a graphical partition manager
        if backend.xlist("testfor gparted")[0]:
            self.gparted = "gparted"
#TODO: Is 'partitionmanager' the right command?
        elif backend.xlist("testfor partitionmanager")[0]:
            self.gparted = "partitionmanager"
        else:
            self.gparted = None
        ui.command("disks:guipart.enable", self.gparted != None)


    def init(self):
        # If devices are added (by writing partition tables to blank devices)
        # the detection process should be repeated, so a loop is used
        rex = re.compile(r"Error: *(/dev/[^:]*): *unrec[^:]*label")
        for round in (0, 1):
            newdev = False
            ld = backend.xlist("get-devices")
            # Note that if one of these has mounted partitions it will not be
            # available for automatic partitioning, and should thus not be
            # included in the list used for automatic installation
            lines = []
            for line in ld[1]:
                # In virtualbox with a fresh virtual disk, we can get this:
                # "Error: /dev/sda: unrecognised disk label:"
                # but the output line is pretty mangled, so it needs filtering
                m = rex.search(line)
                if m:
                    if round > 0:
                        # Don't offer formatting on second round
                        continue
                    dev = m.group(1)
                    if ui.confirmDialog(_("Error scanning devices: "
                            "unrecognised disk label\n\n"
                            "Your disk (%s) seems to be empty and unformatted. "
                            "Shall I prepare it for use (create an msdos "
                            "partition table on it)?")
                            % dev):
                        if backend.xlist("make-parttable %s" % dev)[0]:
                            newdev = True
                        else:
                            run_error(_("Couldn't create partition table on %s" % dev))
                else:
                    lines.append(line)

            if not newdev: break

        if lines:
            mounts = backend.xlist("get-mounts")[1]
            self.devices = []
            for dsn in lines:
                d, s, n = [i.strip() for i in dsn.split(":")]
                # Determine devices which have mounted partitions
                dm = '+'
                for m in mounts:
                    if m.startswith(d):
                        dm = '-'
                        break
                self.devices.append((dm, d, s, n))

        else:
            fatal_error(_("No disk(-like) devices were found,"
                    " so larchin cannot proceed."))
            return False

        if len(self.devices) <= self.device_index:
            self.device_index = 0
        ui.command("disks:device-list.set", self.devices, self.device_index)
        ui.command("disks:device-list.compact")
        #self.select_device(self.device_index)


    def select_device(self, index):
        self.device_index = index
        self.device = self.devices[index][1]
        di = DiskInfo(self.device)
        # Convert size from cyls to GB
        c2G = float(di.cyl2B()) / 10**9
        parts = di.parts
        pinfo = []
        for p in parts:
            size = "%-7.2f" % ((p[2]-p[1]+1)*c2G)
            pinfo.append((p[0], size, p[4]))
        ui.command("disks:device-partitions.set", pinfo)
        ui.command("disks:device-partitions.compact")

#TODO: test this ...
        # Use blkid to test whether 1st partition is NTFS
        t1 = backend.xlist("get-blkinfo TYPE %s1" % self.device)
        self.ntfs1 = t1[0] and (t1[1][0] == "ntfs")
        ui.command("disks:ntfs-shrink.enable", self.ntfs1)

        # If device has mounted partition(s), it is not autopartitionable
        #Might be useful for testing: noauto = False
        noauto = (self.devices[index][0] == '-')

        size = self.devices[index][2]
        if size.endswith("GB"):
            if float(size[:-2]) < 10.0:
                noauto = True
        else:
            noauto = True
        ui.command("disks:auto.enable", not noauto)
        if (self.method == "auto") and noauto:
            ui.command("disks:nopart.set", True)
        self.setkeep1(self.ntfs1 and
                (self.method == "auto") and not noauto)


    def auto_toggle(self, on):
        if on:
            self.method = "auto"
            self.setkeep1(self.ntfs1)
        else:
            self.setkeep1(False)

    def keep1_toggle(self, on):
        self.keep1 = on

    def setkeep1(self, on):
        ui.command("disks:keep1.set", on)
        ui.command("disks:keep1.enable", on)
        self.keep1_toggle(on)

    def guipart_toggle(self, on):
        if on:
            self.method = "guipart"

    def cfdisk_toggle(self, on):
        if on:
            self.method = "cfdisk"

    def nopart_toggle(self, on):
        if on:
            self.method = ""


    def ok(self):
        if self.method == "auto":
            command.runsignal("&auto-partition&", self.device, self.keep1)
        elif self.method == "guipart":
            command.runsignal("&gui-partition&", self.gparted, self.device)
        elif self.method == "cfdisk":
            command.runsignal("&cfdisk-partition&", self.device)
        else:
            command.runsignal("&manual-partition&", self.device)

