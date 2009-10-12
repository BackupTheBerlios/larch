# autopart.py - Automatic partitioning and mount-point selection
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
# 2009.10.12

doc = _("""
<h2>Automatic Partitioning</h2>
<p>To make straightforward installations easier it is possible to choose
a simple automatic division of your disk drive for the Arch Linux installation.
</p>
<p>WARNING: If you have an operating system already installed on this drive
which you wish to keep, you must perform partitioning manually (or use the
existing partitions) by selecting 'Edit disk partitions manually' (or
'Select Installation Partitions') from the stage menu.
</p>
<p>EXCEPTION: if the existing operating system uses the NTFS file-system
(Windows), it is also possible to use automatic partitioning, if enough
space is free, or has been freed by deleting or shrinking one or more NTFS
partitions. At present this method only supports retention of the first
disk partition.
</p>
<h3>Swap Partition</h3>
<p>You can choose to allocate space for a swap partition, which is especially
useful if you don't have a lot of memory installed, or if you want to use
'suspend-to-disk' (which must be set up separately, larchin itself does not
set it up). It is difficult to say how much space you should allocate for
a swap partition, it depends on your system and your usage patterns.
</p>
<h3>Partition for User Data</h3>
<p>If you have enough free space on your device you also have the option of
creating a separate partition for user data. This allows you to keep your data
separate from the system files, so that the operating system can later be
reinstalled without destroying your data. Traditionally this partition is
mounted at /home, so all user files reside on it, but there are some advantages
to using a different mount point. One potential advantage is that the
configuration files for the system and various applications which are saved in
a user's home directory (and which may cause problems if used by other systems,
e.g. after a reinstallation) can easily be kept separate from the user's
personal data. Here /data is offered as an alternative to /home.
</p>""")


class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&auto-partition&", self.select_page),
                ("autopart:free*changed", self.freesizechanged),
                ("autopart:swapsize*changed", self.swapsizechanged),
                ("autopart:swap*toggled", self.swaptoggled),
                ("autopart:homesize*changed", self.homesizechanged),
                ("autopart:home*toggled", self.hometoggled),
            ]

    def __init__(self, index):
        self.page_index = index
        ui.newwidget("Label", "autopart:disk_l", text=_("Device:"))
        ui.newwidget("LineEdit", "autopart:disk", ro=True)
        ui.newwidget("Label", "autopart:disksize_l",
                text=_("Total device capacity:"))
        ui.newwidget("LineEdit", "autopart:disksize", ro=True)
        ui.newwidget("Label", "autopart:free_l",
                text=_("Leave unallocated:"))
        ui.newwidget("SpinBox", "^autopart:free", decimals=0, min=0.0,
                tt=_("You can choose to leave some of the space unallocated"))
        ui.newwidget("Label", "autopart:reserved_l",
                text=_("Reserved space:"))
        ui.newwidget("LineEdit", "autopart:reserved", ro=True,
                tt=_("Space not available because a Windows partition is to be retained"))

        ui.newwidget("OptionalFrame", "^autopart:swap",
                text=_("Create Swap Partition"))
        ui.newwidget("Label", "autopart:swapsize_l",
                text=_("Swap partition size (GB):"))
        ui.newwidget("SpinBox", "^autopart:swapsize", decimals=1, min=0.5,
                tt=_("Enter the desired size for the swap partition here"))
        ui.newwidget("CheckBox", "^autopart:swapcheck", tt=_(tt_seedocs),
                text=_("Check for bad blocks when formatting."
                        " Don't use this in VirtualBox (it takes forever)."))

        ui.newwidget("OptionalFrame", "^autopart:home",
                text=_("Create Separate Partition for User Data"))
        ui.newwidget("Label", "autopart:homesize_l",
                text=_("User data partition size (GB):"))
        ui.newwidget("SpinBox", "^autopart:homesize", decimals=0, min=1.0,
                tt=_("Enter the desired size for the user data partition here"))
        ui.newwidget("CheckBox", "^autopart:homedata", tt=_(tt_seedocs),
                text=_("Create /data instead of /home partition"))

        ui.newwidget("Label", "autopart:syssize_l",
                text=_("Space for Arch root partition:"))
        ui.newwidget("LineEdit", "autopart:syssize", ro=True)

        ui.layout("page:autopart", ["*VBOX*",
                ["*GRID*",
                    ["*+*", "autopart:disk_l", "autopart:disk", ["*SPACE", 100],
                            "autopart:disksize_l", "autopart:disksize"],
                    ["*+*", "autopart:free_l", "autopart:free", "*|",
                            "autopart:reserved_l", "autopart:reserved"]],
                "autopart:swap",
                "autopart:home",
                ["*HBOX*", "*SPACE", "autopart:syssize_l", "autopart:syssize"]
                ])

        ui.layout("autopart:home", ["*VBOX*",
                ["*HBOX*", "autopart:homesize_l", "autopart:homesize"],
                "autopart:homedata"])

        ui.layout("autopart:swap", ["*VBOX*",
                ["*HBOX*", "autopart:swapsize_l", "autopart:swapsize"],
                "autopart:swapcheck"])

    def select_page(self, device, keep1):
        self.device = device
        self.keep1 = keep1
        command.pageswitch(self.page_index,
                _("Automatic Partitioning"))

    def setup(self):
        self.systemsize = self.get_system_size_estimate()
        self.memsize = float(backend.xlist("get-memsize")[1][0]) * 1024 / 10**9


#TODO
    def init(self):
        # Info on drive
        partsizes = backend.xlist("partsizes " + self.device)[1]
        assert len(partsizes) > 1
        self.disksize = float(partsizes[0].split()[1]) * 1024 / 10**9
        self.p1size = (float(partsizes[1].split()[1]) * 1024.0 / 10**9
                if self.keep1 else 0.0)
        ui.command("autopart:disk.x__text", self.device)
        ui.command("autopart:disksize.x__text", "%4.0f GB" % self.disksize)
        ui.command("autopart:reserved.x__text", "%4.0f GB" % self.p1size)
        # Set up unallocated space display
        self.unallocated = 0.0
        self.maxunallocated = self.disksize - self.p1size - self.systemsize - 15.0
        # Also use this as criterion for possibility of user data partition
        self.datapart = self.maxunallocated > 0.0
        ui.command("autopart:free.enable", self.datapart)
        ui.command("autopart:free_l.enable", self.datapart)
        ui.command("autopart:home.enable", self.datapart)
        if self.datapart:
            ui.command("autopart:free.x__max", self.maxunallocated)
            ui.command("autopart:free.x__value", 0.0)
            self.datasize = self.maxunallocated + 5.0
            self.datasize_old = self.datasize
            if self.datasize > 20.0:
                ui.command("autopart:home.opton", True)
                ui.command("autopart:homesize.x__max", self.datasize)
                ui.command("autopart:homesize.x__value", self.datasize)
            else:
                self.datasize = 0
                ui.command("autopart:home.opton", False)
        else:
            self.datasize = 0.0
        # Set up swap partition display
        ui.command("autopart:swap.opton", True)
        self.swapsize = 1.0
        self.swapsize_old = 1.0
        self.recalculate()


    def recalculate(self):
        self.freesize = (self.disksize - self.p1size - self.unallocated
                - self.systemsize - 5.0)

        # Set up swap partition display
        if self.swapsize:
            maxswap = round(self.memsize + 0.5) if self.memsize > 2.0 else 2.0
            if (self.freesize - maxswap) < 10.0:
                maxswap = 1.0
            ui.command("autopart:swapsize.x__max", maxswap)
            if self.swapsize > maxswap:
                self.swapsize = maxswap
            ui.command("autopart:swapsize.x__value", self.swapsize)

        # Set up data partition display
        if self.datapart:
            maxdata = self.freesize - self.swapsize
            if maxdata > 30.0:
                maxdata = maxdata - 10.0
            elif maxdata > 10.0:
                maxdata = 5.0 + maxdata/2
            ui.command("autopart:homesize.x__max", maxdata)
            if self.datasize > maxdata:
                self.datasize = maxdata
                ui.command("autopart:homesize.x__value", maxdata)

        self.rootsize = (self.disksize - self.p1size - self.unallocated
                - self.swapsize - self.datasize)
        ui.command("autopart:syssize.x__text", "%5.1f GB" % self.rootsize)


#TODO
    def get_system_size_estimate(self):
        return 5.0


    def freesizechanged(self, size):
        self.unallocated = size
        self.recalculate()

    def swaptoggled(self, on):
        if on:
            self.swapsize = self.swapsize_old
        else:
            self.swapsize_old = self.swapsize
            self.swapsize = 0.0
        self.recalculate()

    def swapsizechanged(self, size):
        self.swapsize = size
        self.recalculate()

    def hometoggled(self, on):
        if on:
            self.datasize = self.datasize_old
        else:
            self.datasize_old = self.datasize
            self.datasize = 0.0
        self.recalculate()

    def homesizechanged(self, size):
        self.datasize = size
        self.recalculate()





#TODO: ok method
# This forward method is still from the old version
    def forward(self):
        if not popupWarning(_("You are about to perform a destructive"
                " operation on the data on your disk drive (%s):\n"
                "    Repartitioning (removing old and creating new"
                " partitions)\n\n"
                "This is a risky business, so don't proceed if"
                " you have not backed up your important data.\n\n"
                "Continue?") % self.device):
            return -1

        # I'll make the sequence: root, then swap then home.
        # But swap and/or home may be absent.
        # Start partitioning from partition with index self.startpart,
        # default value (no NTFS partitions) = 1.
        # The first sector to use is self.startsector
        # default value (no NTFS partitions) = 0.

        # The actual partitioning should be done, but the formatting can
        # be handled - given the appropriate information - by the
        # installation stage.

        # Remove all existing partitions from self.startpart
        install.rmparts(self.device, self.startpart)

        secspercyl = self.dinfo[2]
        startcyl = (self.startsector + secspercyl - 1) / secspercyl
        endcyl = self.dinfo[1]
        # Note that the ending cylinder referred to in the commands
        # will not be included in the partition, it is available to
        # be the start of the next one.

        # Get partition sizes in cylinder units
        ncyls = endcyl - startcyl
        cylsizeB = secspercyl * self.dinfo[3]
        swapC = int(self.swapsizeG * 1e9 / cylsizeB + 0.5)
        homeC = int(self.homesizeG * 1e9 / cylsizeB + 0.5)
        rootC = ncyls - swapC - homeC

        startcyl = self.newpart(startcyl, endcyl, rootC,
                (swapC == 0) and (homeC == 0))
        # See partition formatting and fstab setting up for the
        # meaning of the flags
        config = "/:%s%d:%s:%s:%s" % (self.device, self.startpart,
                install.DEFAULTFS, install.FORMATFLAGS, install.MOUNTFLAGS)
        self.startpart += 1
        if (swapC > 0):
            format = "cformat" if self.getCheck(self.swapfc) else "format"
            startcyl = self.newpart(startcyl, endcyl, swapC,
                    (homeC == 0), True)
            install.set_config("swaps", "%s%d:%s:include" %
                    (self.device, self.startpart, format))
            self.startpart += 1

        if (homeC > 0):
            startcyl = self.newpart(startcyl, endcyl, homeC, True)
            config += "\n/home:%s%d:%s:%s:%s" % (self.device, self.startpart,
                    install.DEFAULTFS, install.FORMATFLAGS, install.MOUNTFLAGS)

        install.set_config("partitions", config)
        return 0

    def newpart(self, startcyl, endcyl, size, last, swap=False):
        """Add a new partition, taking primary/extended/logical into
        account.
        """
        # Use install.makepart, passing the cylinder boundaries
        part = -1
        if (self.startpart == 4) and not last:
            self.startpart = 5
            install.makepart(self.device, 0, startcyl, endcyl)
        elif (self.startpart <= 4):
            part = self.startpart

        newstartcyl = startcyl + size
        install.makepart(self.device, part,
                startcyl, newstartcyl,
                swap)

        return newstartcyl



