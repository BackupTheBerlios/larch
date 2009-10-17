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
# 2009.10.17

from backend import DiskInfo

doc = _("""
<h2>Automatic Partitioning</h2>
<p>To make straightforward installations easier it is possible to choose
a simple automatic division of your disk drive for the <em>Arch Linux</em>
installation.
</p>
<p>WARNING: If you have an operating system already installed on this drive
which you wish to keep, you must perform partitioning manually (or use the
existing partitions) by selecting 'Edit disk partitions manually' (or
'Select Installation Partitions') from the stage menu.
</p>
<p>EXCEPTION: if the existing operating system uses the NTFS file-system
(<em>Windows</em>), it is also possible to use automatic partitioning, if
enough space is free, or has been freed by deleting or shrinking one or
more NTFS partitions. At present this method only supports retention of
the first disk partition.
</p>
<h3>Swap Partition</h3>
<p>You can choose to allocate space for a swap partition, which is especially
useful if you don't have a lot of memory installed, or if you want to use
'suspend-to-disk' (which must be set up separately, <em>larchin</em> itself
does not set it up). It is difficult to say how much space you should allocate
for a swap partition, it depends on your system and your usage patterns.
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
                ("&auto-partition!", self.select_page),
                ("autopart:free*changed", self.freesizechanged),
                ("autopart:swapsize*changed", self.swapsizechanged),
                ("autopart:swap*toggled", self.swaptoggled),
                ("autopart:homesize*changed", self.homesizechanged),
                ("autopart:home*toggled", self.hometoggled),
                ("&autopartition-run&", self.partition),
                ("autopart:swapcheck*toggled", self.swapcheck_toggle),
                ("autopart:homedata*toggled", self.homedata_toggle),
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

    def setup(self):
        self.systemsize = self.get_system_size_estimate()
        self.memsize = float(backend.xlist("get-memsize")[1][0]) * 1024 / 10**9


    def select_page(self, init, *args):
        self.initialize = init
        if init:
            self.device, self.keep1 = args
        command.pageswitch(self.page_index,
                _("Automatic Partitioning"))


    def init(self):
        if not self.initialize:
            return
        # Info on drive
        di = DiskInfo(self.device)
        c2G = float(di.cyl2B()) / 10**9
        self.disksize = di.drvcyls * c2G
        if self.keep1:
            p = di.parts[0]
            self.p1size = (p[2]-p[1]+1)*c2G
        else:
            self.p1size = 0.0
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

        self.swapcheck = False
        ui.command("autopart:swapcheck.set", False)
        self.homedata = False
        ui.command("autopart:homedata.set", False)


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


    def swapcheck_toggle(self, on):
        self.swapcheck = on


    def homedata_toggle(self, on):
        self.homedata = on


    def ok(self):
        ui.confirmDialog(_("You are about to perform a destructive"
                " operation on the data on your disk drive (%s):\n"
                "    Repartitioning (removing old and creating new"
                " partitions)\n\n"
                "This is a risky business, so don't proceed if"
                " you have not backed up your important data.\n\n"
                "Continue?") % self.device, async="&autopartition-run&")


    def partition(self, doit):
        if not doit:
            return
        # I'll make the sequence: root, then swap then home/data.
        # But swap and/or home may be absent.
        # root and swap are created as primary partitions, home/data
        # as logical (to ensure that ny unallocated space may also be used).

        # The actual partitioning is done, but the formatting is
        # handled - given the appropriate information - by the
        # installation stage. If a swap partition is created that will,
        # however, be formatted.

        startpart = 2 if self.keep1 else 1
        # Remove all existing partitions from startpart
        ui.progressPopup.start()
        ui.progressPopup.add(_("Removing all partitions on %s,\n"
                "   starting from number %d") % (self.device, startpart))
        if not backend.rmparts(self.device, startpart):
            return

        diskinfo = DiskInfo(self.device)
        # Check that the free space corresponds to what is expected.
        # Convert GB to cylinders for (self.disksize - self.p1size)
        allfreecyls = diskinfo.get_freecyls()
        bytespercyl = diskinfo.cyl2B()
        deviation = abs(self.disksize - self.p1size -
                (allfreecyls * bytespercyl / 10**9))
        if deviation > 1:
            fatal_error("BUG in autopart: free space deviation = %5.1f"
                    % deviation)

        # Allocate number of cylinders for the largest partition last,
        # just in case it gets tight ...
        newparts = []
        maxp = None
        maxs = 0
        for m, s, t in (
                ("/", self.rootsize, "primary"),
                ("swap", self.swapsize, "primary"),
                ("/data" if self.homedata else "/home", self.datasize, "logical"),
                ("", self.unallocated, None)):
            if s > 0.1:
                # Convert GB to cylinders
                entry = [t, int((s * 10**9 / bytespercyl) + 0.5), m]
                newparts.append(entry)
                if s > maxs:
                    maxs = s
                    maxp = entry
        sum = 0
        for ps in newparts:
            if ps != maxp:
                sum += ps[1]
        maxp[1] = allfreecyls - sum

        # Create the partitions
        iparts = []
        for t, s, m in newparts:
            if not t:
                continue
            swap = (m=="swap")
            ui.progressPopup.add(_("Creating %s partition for %s")
                    % (t, m))
            part = backend.newpart(self.device, t.startswith("p"), s, swap)
            if not part:
                iparts = None
                break
            if swap and not backend.mkswap(part, self.swapcheck):
                iparts = None
                break
            else:
                # [mount-point, device, size, format]
                iparts.append([m, part, "" if swap else "ext4"])
                ui.progressPopup.add("   ---> " + part)
        ui.progressPopup.end()

        # Go to installation stage
        if iparts:
            command.runsignal("&install!", iparts)
