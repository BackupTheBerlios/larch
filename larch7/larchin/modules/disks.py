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
# 2009.09.29


doc = _("""
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
                (":disks-device-list*select", self.select_device),
                ("&device-select&", self.select_page),
                (":auto*toggled", self.auto_toggle),
                (":guipart*toggled", self.guipart_toggle),
                (":cfdisk*toggled", self.cfdisk_toggle),
                (":nopart*toggled", self.nopart_toggle),
            ]

    def __init__(self, index):
        self.page_index = index
        self.device_index = 0
        ui.command(":disks-device-list.setHeaders", ["", _("Device"),
                _("Size"), _("Model")])
        ui.command(":disks-device-partitions.setHeaders", [_("Partition"),
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
        ui.command(":guipart.enable", self.gparted != None)


    def select_page(self):
        command.pageswitch(self.page_index)


    def init(self):
        count = 0
        while True:
            ld = backend.xlist("get-devices")
            debug(repr(ld))
            # Note that if one of these has mounted partitions it will not be
            # available for automatic partitioning, and should thus not be
            # included in the list used for automatic installation
            lines = []
#TODO: Test this with fresh disk in virtualbox ...
            for line in ld[1]:
                # In virtualbox with a fresh virtual disk, we can get this:
                # "Error: /dev/sda: unrecognised disk label:"
                em = line.split(":")
                if ((em[0].strip() == "Error") and (em[2].strip() ==
                        "unrecognised disk label")):
                    if count < 0:
                        # Don't offer formatting on second round
                        continue
                    dev = em[1].strip()
                    if ui.confirmDialog(_("Error scanning devices:\n %s\n"
                            "Your disk (%s) seems to be empty and unformatted. "
                            "Shall I prepare it for use (create an msdos "
                            "partition table on it)?")
                            % (line, dev)):
                        if xlist("make-parttable %s" % dev)[0]:
                            count += 1
                        else:
                            run_error(_("Couldn't create partition table on %s" % dev))
                else:
                    lines.append(line)

            if count <= 0:
                break
            count = -1

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
        ui.command(":disks-device-list.set", self.devices, self.device_index)
        ui.command(":disks-device-list.compact")
        #self.select_device(self.device_index)


    def select_device(self, index):
        self.device_index = index
        self.device = self.devices[index][1]
        parts = backend.xlist("listparts %s" % self.device)[1]
        pinfo = []
        for p in parts:
            ps = p.split(None, 4)
            if ps[1] != "0":
                # Convert size from MiB to GB
                size = "%-7.2f" % (float(ps[1]) * 10**3 / 2**20)
                pinfo.append((ps[0], size, ps[4]))
        ui.command(":disks-device-partitions.set", pinfo)
        ui.command(":disks-device-partitions.compact")

#TODO: test this ...
        # Use blkid to test whether 1st partition is NTFS
        t1 = backend.xlist("get-blkinfo TYPE %s1" % self.device)
        self.ntfs1 = t1[0] and (t1[1][0] == "ntfs")
        ui.command(":ntfs-shrink.enable", self.ntfs1)

        # If device has mounted partition(s), it is not autopartitionable
        noauto = (self.devices[index][0] == '-')

        size = self.devices[index][2]
        if size.endswith("GB"):
            if int(size[:-2]) < 10:
                noauto = True
        else:
            noauto = True
        ui.command(":auto.enable", not noauto)
        if (self.method == "auto") and noauto:
            ui.command(":nopart.set", True)
        ui.command(":keep1.enable", (self.method == "auto") and not noauto)


    def auto_toggle(self, on):
        if on:
            self.method = "auto"
            ui.command(":keep1.enable", self.ntfs1)
        else:
            ui.command(":keep1.enable", False)

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
            command.runsignal("&auto-partition&", self.device)
        elif self.method == "guipart":
            command.runsignal("&gui-partition&", self.gparted, self.device)
        elif self.method == "cfdisk":
            command.runsignal("&cfdisk-partition&", self.device)
        else:
            command.runsignal("&manual-partition&", self.device)

