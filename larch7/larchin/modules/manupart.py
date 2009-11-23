# manupart.py - Manual disk partitioning and mount-point selection
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
# 2009.11.06

from backend import DiskInfo

doc = _("""
<h2>Manual Partitioning</h2>
<p>This tool allow deletion and creation of partitions, setting of
partition types and mount-points, specification of a file-system type
for a partition (i.e. with which it will be formatted). The actual
formatting takes place at a later stage, except for swap partitions
which are formatted when they are created. Apart from the mount points
and formatting it works a bit like a stripped down cfdisk, also in that
the actual changes are only made when you click on the confirmation
button.
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
personal data. Here /home/DATA is offered as an alternative to /home.
</p>
<h3>Boot Partition</h3>
<p>It is often a good idea to create a boot partition, generally formatted
as ext2. Some file-system types (ext4?) may not be directly bootable
from GRUB, in which case a separate boot partition would be necessary.
But larchin also offers the possibility of installing the <em>live</em>
system to the boot partition (without decompressing it), so that it can
act as a rescue/recovery/maintenance system. This is, however, a
completely different approach to the normal idea of a boot partition - it
will not be mounted as /boot in the installed system and the installed
system's kernel will not reside on this partition. To make this clear
such a partition gets 'liveboot' as its mount-point (without '/' - it
will not be mounted in the newly installed main system).
</p>
<p>It is also possible to specify that only the 'liveboot' ('frugal')
install is to be carried out, by specifying no further mount-points.
</p>""")


class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&manual-partition!", self.select_page),
                ("manu:part-list*select", self.select_part),


            ]

    def __init__(self, index):
        self.page_index = index
        self.run0 = True
        self.memsize = float(backend.memsize()) / 10**9     # GB
        self.larchboot = False


    def buildgui(self):
        ui.widget("Label", "manupart:disk_l", text=_("Device:"))
        ui.widget("LineEdit", "manupart:disk", ro=True)
        ui.widget("Label", "manupart:disksize_l",
                text=_("Total device capacity:"))
        ui.widget("LineEdit", "manupart:disksize", ro=True)
        ui.widget("List", "^manu:part-list", selectionmode="Single",
                tt=_("Select the partition (or free space) to alter"))


        ui.layout("page:manupart", ["*VBOX*",


    def select_page(self, init, device=None):
        self.initialize = init
        if init:
            self.device = device
            if self.run0:
                self.run0 = False
                self.buildgui()

        command.pageswitch(self.page_index,
                _("Manual Partitioning"))


    def init(self):
        # Info on drive
        di = DiskInfo(self.device)
        c2G = float(di.cyl2B()) / 10**9
        self.disksize = di.drvcyls * c2G
        ui.command("manupart:disk.x__text", self.device)
        ui.command("manupart:disksize.x__text", "%4.0f GB" % self.disksize)








    def get_system_size_estimate(self):
        """Assume 3*medium_size for the installation, the rest being for
        the boot partition.
        """
        self.live_gb = float(backend.get_medium_size_estimate()) / 1000
        return 4.5 * self.live_gb




    def ok(self):
#TODO
# If I am just assigning mount-points and formats this is actually
# not desirable.
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
        # I'll make the sequence: root, then swap then home(/DATA).
        # But swap and/or home may be absent.
        # root and swap are created as primary partitions, home(/DATA)
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
        boots = 0.2
        if self.larchboot:
            boots += self.live_gb * 1.5
        for m, s, t in (
                ("/boot", boots, "primary"),
                ("swap", self.swapsize, "primary"),
                ("/", self.rootsize, "logical"),
                ("/home/DATA" if self.homedata else "/home", self.datasize,
                        "logical"),
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
                iparts.append([m, part, "" if swap
                        else "ext2" if m == "/boot"
                        else "ext4"])
                ui.progressPopup.add("   ---> " + part)
        ui.progressPopup.end()

        # Go to installation stage
        if iparts:
            ui.sendsignal("&install!", iparts)
