# ntfs.py - Resizing of NTS partitions
#
# (c) Copyright 2008, 2009 Michael Towers <gradgrind[at]online[dot]de>
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
# 2009.03.23

from stagebase import StageBase
from ntfs_gui import gui_NTFS


class Stage(StageBase, gui_NTFS):
    def getHelp(self):
        return _("If a partition is occupied by a Windows operating system"
                " (using the NTFS file-system), you have here the option of"
                " shrinking it to create enough space for Arch Linux.\n"
                "As the automatic partitioning utility only considers space"
                " after the last NTFS partition, it may under certain"
                " circumstances be necessary to delete such a partition,"
                " which can also be done here.\n"
                "If you need more sophisticated partition management you"
                " will have to resort to the manual tools. This automatic"
                " partitioning is only suitable for situations where space"
                " for the new Linux installation is to be allocated at the"
                " end of a disk, after 0 or more NTFS partitions.\n\n"
                "As the operations offered here are potentially quite"
                " destructive please consider carefully before using them.")


    def __init__(self, name):
        StageBase.__init__(self, name)
        gui_NTFS.__init__(self)


    def init(self):
        # Get a list of NTFS partitions (all disks).
        self.partlist = self.getNTFSparts()
        # If there are none, skip this stage
        if not self.partlist:
            installl.interrupt = "#SKIP"
            return

        # Get info about the disks and partitions:
        # Each disk (with NTFS partitions) gets an entry in self.diskinfo.
        # Each entry is a list: [disk info, list of all partitions' info,
        #    list of NTFS partition numbers in reverse order]
        self.diskinfo = {}
        devs = []
        for p in self.partlist:
            d = p.rstrip("0123456789")
            pnum = int(p[len(d):])
            if self.diskinfo.has_key(d):
                self.diskinfo[d][2].append(pnum)
            else:
                devs.append(d)
                self.diskinfo[d] = [install.getDeviceInfo(d),
                        install.getParts(d), [pnum]]

        # Set gui device list. That should result in a callback to
        # set_device_cb to set up the display for the selected device,
        # which will be the first in the list by default.
        mainWindow.idle_call(self.gui_reset, devs)


    def set_device_cb(self, drive):
        self.drive = drive
        self.dinfo, pilist, parts = self.diskinfo[self.drive]
        self.secsize = self.dinfo[3]

        # self.dinfo:
        #   ( drive size as string,
        #     drive size in cylinders,
        #     cylinder size in sectors,
        #     sector size in bytes )
        # pilist:
        #   [(partition-number, partition-type,
        #     size in sectors, start in sectors, end in sectors),
        #    ... ]

        # Display information about disk
        self.gui_show_disksize(self.dinfo[0])
        plist = []
        for p in parts:
            psize = None
            for q in pilist:
                if q[0] == p:
                    psize = q[2] * self.secsize / 1e9
                    break
            plist.append(["%s%d" % (self.drive, p), psize])
        self.gui_show_parts(plist)

        # Get information on the current partition
        self.pnum = parts[0]
        for pi in pilist:
            if (pi[0] == self.pnum):
                # These sizes are all in sectors
                self.psize, self.pstart, self.pend = pi[2:]
                break

        part = "%s%d" % (self.drive, self.pnum)
        plog("NTFS editor: %s" % part)

        self.dsize = self.dinfo[1] * self.dinfo[2]  # sectors
        self.psizeG = float(self.psize) * self.secsize / 1e9

        # Set the maximum shrunk size to slightly less than the
        # current partition size
        self.maxsizeG = self.psizeG - 0.2
        plog("reduced psize = %d GB" % self.maxsizeG)

        # Get occupied space, allow 200MB extra
        self.minsizeG = float(install.getNTFSmin(part)) / 1e9 + 0.2
        plog("NTFS: max. shrink to %3.1f GB" % self.minsizeG)
        # Too full to shrink?
        self.toofull = (self.maxsizeG < self.minsizeG)

        if self.toofull:
            self.gui_set_delete(
                    ((self.dsize-self.pend) * self.secsize / 1e9)
                            < install.LINUXMIN)
            return

        # Whether to shrink by default?
        # Only if a fair sharing of free space calls for shrinking,
        # but if it is impossible to shrink to the required extent
        # one should suggest deleting the partition.
        # Suggest sharing excess (over the minimum) equally between
        # Linux and Windows
        shrinkon = True
        sizeG = (self.psizeG + self.minsizeG) / 2
        excess = ((self.dsize - self.pstart) * self.secsize / 1e9
                - self.minsizeG
        if excess < install.LINUXMIN:
            # The available space is too small, propose
            # deleting the partition
            self.gui_set_delete(True)
            sizeG = self.minsizeG
        else:
            self.gui_set_delete(False)
            excess -= install.LINUXMIN
            s = self.minsizeG + (excess / 2)
            if (s < (self.psizeG - 0.5)):
                # shrink unless change is only minimal
                sizeG = s
            else:
                shrinkon = False
        self.gui_shrinkinit(shrinkon, sizeG)


    def getNTFSparts(self):
        """Return a list of NTFS partitions. Only unmounted partitions will
        be considered.
        """
        # Get list of mounted partitions
        mounts = [m.split()[0] for m in install.getmounts().splitlines()
                if m.startswith('/dev/')]

        # Get and filter list of NTS partitions
        partlist = [p for p in install.listNTFSpartitions()
                if p not in mounts]

        # Reverse the list order so that the last partitions come first
        partlist.reverse()
        return partlist


    def ok(self):
# Note that I am reading from the gui here without wrapping the calls.
# I am guessing that this will be harmless, but it needs to be checked.
        devpart="%s%d" % (self.drive, self.pnum)
        if self.gui_deleteflag():
            install.rmpart(self.drive, self.pnum)


        elif self.gui_shrinkflag() and self.popupWarning(
                _("You are about to shrink %s."
                " Make sure you have backed up"
                " any important data.\n\n"
                "Continue?") % devpart):
            newsize = int(self.gui_size() * 1e9 / self.secsize)  # sectors
            message = install.doNTFSshrink(self.drive, self.pnum,
                    newsize, self.pstart, self.dinfo)
            if message:
                # resize failed
                self.popupMessage(_("Sorry, resizing failed. Here is the"
                        " error report:\n\n") + message)

        return


    def get_rest_size_cb(self):
        """Called when the requested shrinkage changes, by moving the slider,
        by changing the delete flag, by changing the shrink flag.
        If delete partition, count from start of partition to end of disk;
        elif shrink partition, count from new end of partition to end of disk;
        else count from old end of partition to end of disk.
        """
        if self.gui_deleteflag():
            # This could be wrong, if there is free space before the partition
            rest = self.dsize - self.pstart
        elif self.gui_shrinkflag():
            rest = self.dsize - self.pstart - int(size * 1e9 / self.secsize)
        else:
            rest = self.dsize - self.pend
        return "%8.1f GB" % (float(rest) * self.secsize / 1e9)

