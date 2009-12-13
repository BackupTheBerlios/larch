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
# 2009.12.13

from backend import DiskInfo

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
select manual partitioning. The most advanced partition editing option
('Advanced graphical partition manager') uses one of the external tools
gparted or (kde's) partitionmanager, if available.
</p>
<p>The internal manual partitioner also handles selection of the mount
points, so even if you use the advanced option you must complete the
partitioning with the internal partitioner (but not if the automatic
partitioning option is used).
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
                ("device-select!", self.select_page),
                ("disks:device-list*select", self.select_device),
                ("disks:auto*toggled", self.auto_toggle),
                ("disks:guipart*toggled", self.guipart_toggle),
                ("disks:manual*toggled", self.manual_toggle),
                ("disks:keep1*toggled", self.keep1_toggle),
            ]

    def __init__(self, index):
        self.page_index = index
        self.device_index = 0
        self.method = ""
        self.run0 = True


    def buildgui(self):
        ui.widget("List", "^disks:device-list", selectionmode="Single",
                tt=_("Select the device to inspect, or for partitioning"))
        ui.widget("List", "disks:device-partitions", selectionmode="None",
                tt=_("The partitions on the selected device"))

        ui.widget("Button", "^disks:ntfs-shrink",
                text=_("Shrink first partition (Windows - NTFS)"))
        ui.widget("CheckBox", "^disks:keep1",
                text=_("Keep first partition (Windows - NTFS)"))

        ui.widget("Frame", "disks:choose_partition_method",
                text=_("Choose Partitioning Method"))
        ui.widget("RadioButton", "^disks:auto",
                text=_("Autopartition and install to selected device"))
        ui.widget("RadioButton", "^disks:guipart",
                text=_("Advanced graphical partition manager"))
        ui.widget("RadioButton", "^disks:manual",
                text=_("Manual partitioning OR use existing partitions"))

        ui.layout("disks:choose_partition_method", ["*HBOX*",
                ["*VBOX*", "disks:auto", "disks:guipart", "disks:manual"],
                ["*SPACE", 50],
                ["*VBOX*", "disks:keep1", "disks:ntfs-shrink", "*SPACE"]])
        ui.layout("page:disks", ["*VBOX*",
                ["*HBOX*", "disks:device-list", "disks:device-partitions"],
                "*SPACE", "disks:choose_partition_method"])

        ui.command("disks:device-list.setHeaders", ["", _("Device"),
                _("Size"), _("Model")])
        ui.command("disks:device-partitions.setHeaders", [_("Partition"),
                _("Size (GB)"), _("Type")])

        ui.command("disks:guipart.enable", self.gparted != None)


    def select_page(self, init):
        if self.run0:
            self.run0 = False
            # Test for a graphical partition manager
            if backend.available("gparted"):
                self.gparted = "gparted"
            elif backend.available("partitionmanager"):
                self.gparted = "partitionmanager"
            else:
                self.gparted = None
            self.buildgui()

        command.pageswitch(self.page_index,
                _("Disk information and selection"))


    def init(self):
        disks = backend.get_devices()
        if disks:
            mounts = backend.get_mounts()
            self.devices = []
            for d, s, n in disks:
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
        return True


    def select_device(self, index=-1):
        if index < 0:
            return
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

        # Test whether 1st partition is NTFS
        self.ntfs1 = backend.get_partfstype(self.device + "1") == "ntfs"
        ui.command("disks:ntfs-shrink.enable", self.ntfs1)

        # If device has mounted partition(s), it is not autopartitionable
        # Might be useful for testing: noauto = False
        noauto = (self.devices[index][0] == '-')

        size = self.devices[index][2]
        if size.endswith("GB"):
            if float(size[:-2]) < 10.0:
                noauto = True
        else:
            noauto = True
        ui.command("disks:auto.enable", not noauto)
        if not self.method:
            ui.command("disks:%s.set" % ("manual" if noauto else "auto"),
                    True)
        elif (self.method == "auto") and noauto:
            method = ui.command("disks:manual.set", True)
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

    def manual_toggle(self, on):
        if on:
            self.method = "manual"


    def ok(self):
        if self.method == "auto":
            ui.sendsignal("auto-partition!", self.device, self.keep1)
        elif self.method == "guipart":
            backend.xlist("runcom", self.gparted, self.device)
        else:
            ui.sendsignal("manual-partition!", self.device)

