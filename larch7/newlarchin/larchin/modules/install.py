# install.py
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
# 2009.03.25

"""This module handles communication with the system on which Arch is to
be installed, which can be different to the one on which larchin is
running. The installation machine is accessed through bash scripts, in
the separate package 'larchin-syscalls', which must of course be
installed on it.
This communication takes place in a thread separate from the main gui
thread, so interaction with the gui is not completely straightforward, it
is handled mainly by idle-calls.
Problems are signalled to the main thread via the variables install.error
(a message, which should be set first) and 'assert False'.
'assert False, <message>' can be used to trap bugs, i.e. errors which
should not occur (i.e. which should result in code fixes).
"""

import os, shutil, signal
import re
import crypt, random

import dialogs
from threadcom import ThreadMessaging
from backend import Backend


class installClass(Backend, ThreadMessaging):
    def __init__(self, host):
        Backend.__init__(self, host)
        ThreadMessaging(self)

        self.LINUXMIN = 5.0     # GB, guessed min. space requirement for Linux

        # The following flag declarations serve two purposes:
        #  1) Show which flags are available
        #  2) Show the defaults ('on' is capitalized)
        # Flags used to affect partition formatting (fs-type dependent usage):
        # ext3/4::: i:directory indexing, f: full journal
        self.FORMATFLAGS = "If"
        # Flags used to set mount options in /etc/fstab:
        # a: noatime, m: noauto
        self.MOUNTFLAGS = "Am"
        # Default file-system for automatic partitioning
        self.DEFAULTFS = "ext3"

        # Available file-systems for formatting
        self.filesystems = ['ext3', 'ext4', 'reiserfs', 'ext2', 'jfs', 'xfs']
        # List of mount-point suggestions
        self.mountpoints = ['---', '/', '/home', '/boot', '/var',
                '/opt', '/usr']

        # By default use UUID for partitions, and for swap (if
        # there is one). A problem with using UUID for swaps is that the
        # partition might get reformatted by another installation,
        # which would probably change the UUID!
        self.use_uuid = True
        self.use_uuid_swap = True

        # Create a directory for temporary files
        shutil.rmtree("/tmp/larchin", True)
        os.mkdir("/tmp/larchin")

        # For inter-thread communication of errors, etc.
        self.error = None
        self.interrupt = None


    def exit(self):
        """Tidy up and quit the program. This should be called only from
        the main (gui) thread.
        """
        self.cancel()
        self.tidyup()
        mainWindow.exit()


    def tidyup(self):
        tu = self.xcall("tidyup")
        if tu:
            dialogs.popupError(tu, _("Tidying up failed,"
                    " there may still be devices mounted"))
        shutil.rmtree("/tmp/larchin", True)


    def cancel(self):
        self.interrupt = "#CANCEL"
        if self.process:
            plog("!!! BREAK ... killing subprocess")
            try:
                # The process might already have completed, so trap exceptions
                self.process.kill()
            except:
                pass


#-----------------------------------------------------------------------
# The methods below are designed to work in the background thread.


    def set_config(self, item, value):
        fh = open("/tmp/larchin/%s" % item, "w")
        fh.write(value)
        fh.close()


    def get_config(self, item, trap=True):
        f = "/tmp/larchin/%s" % item
        if os.path.isfile(f):
            fh = open(f, "r")
            value = fh.read()
            fh.close()
        else:
            assert not trap, (_("Configuration item not found: %s") % item)
            value = None
        return value


    def quit(self):
        """This is called to signal the desire to quit the program. It
        should cause the program to tidy up and exit, and can
        also be called from any thread without confusing matters, I hope.
        """
        mainWindow.idle_call(self.exit)


    def listDevices(self):
        """Return a list of device descriptions.
        Each device description is a list of strings:
            [device (/dev/sda, etc.),
             size (including unit),
             device type/name]
        """
        devices = []
        op = self.xcall("get-devices")
        for line in op.splitlines():
            # In virtualbox with a fresh virtual disk, we can get this:
            # "Error: /dev/sda: unrecognised disk label:"
            em = line.split(":")
            if (em[0].strip() == "Error" and (em[2].strip() ==
                    "unrecognised disk label")):
                dev = em[1].strip()
                if self.showWarning(_("Error scanning devices:\n %s\n"
                        "Your disk (%s) seems to be empty and unformatted. "
                        "Shall I prepare it for use (create an msdos "
                        "partition table on it)?")
                        % (line, dev)):
                    op = self.xcall("make-parttable %s" % dev)
                    if op:
                        self.error = _("Couldn't create partition table:\n %s")
                        assert False
                    else:
                        return self.listDevices()
                return []
            devices.append(line.rstrip(';').split(':'))
        return devices

    def get_partsize(self, part):
        """Get a human-readable partition size.
        """
        return self.xcall("get-partsize %s" % part)

    def getmounts(self):
        return self.xcall("get-mounts")

    def setDevices(self, devs):
        """Set the self.devices list.
        """
        self.devices = devs

    def larchdev(self):
        """If the running system is larch, return the device from which
        it booted. Otherwise ''.
        """
        return self.xcall("larchbootdev").strip()

    def fdiskall(self):
        """Get the output of 'fdisk -l'
        """
        return self.xcall("fdiskall")

    def getDeviceInfo(self, dev):
        """Get info on drive and partitions (dev="/dev/sda", etc.)
        Return tuple: ( drive size as string,
                        drive size in cylinders,
                        cylinder size in sectors,
                        sector size in bytes )
        """
        dinfo = self.xcall("fdisk-l %s" % dev).splitlines()

        # get the drive size as a string
        ds = re.search(r"%s:([^,]+)" % dev, dinfo[0])
        dsize = ds.group(1)

        # get the drive size in cylinders
        ds = re.search(r",[^,]+,[ ]*([0-9]+)", dinfo[1])
        dcsize = ds.group(1)

        # get cylinder size in sectors and sector size in bytes
        ds = re.search(r"([0-9]+)[ ]*\*[ ]*([0-9]+)", dinfo[2])
        csize = ds.group(1)
        ssize = ds.group(2)

        return (dsize, int(dcsize), int(csize), int(ssize))

    def getParts(self, dev):
        """Get info about the partitions on the given drive.
        Return list of tuples:
            [ (partition-number, partition-type,
               size in sectors, start in sectors, end in sectors),
                         ... ]

        Under certain circumstances (?) the partition-type info seems
        to be unreliable, e.g. a test with three NTFS partitions
        resulted in the third showing an empty type-field.
        """
        pinfo = self.xcall("get-partinfo %s" % dev).splitlines()
        ilist = []
        for l in pinfo:
            pm = re.search(r"^([0-9]+):([0-9]+)s:([0-9]+)s:"
                    "([0-9]+)s:([^\:]*)[;:]", l)
            if pm:
                # Add tuple (partition-number, partition-type,
                #            size in sectors, start in sectors, end in sectors)
                # Free space has partition-number 0 and type 'free'
                p = int(pm.group(1))
                t = pm.group(5)
                if (t == 'free'):
                    p = 0
                ilist.append((p, t, int(pm.group(4)),
                              int(pm.group(2)), int(pm.group(3))))
        return ilist

    def listNTFSpartitions(self):
        """Return a simple list of partitions (on all devices) which are
        of type 'ntfs'.
        """
        return self.xcall("get-ntfs-parts").split()

    def getNTFSinfo(self, part):
        """Return information about the given partition as a tuple:
                (cluster size (unit for resizing?),
                 current volume size,
                 current device size,
                 suggested resize point (minimum))
        All sizes are in bytes.
        When resizing, I suppose it makes sense to select a multiple of
        the cluster size - but this doesn't seem to be necessary. For
        other reasons - it seems to be standard - I have decided to make
        partitions start on (even?) cylinder boundaries.

        If the call fails for some reason, None is returned.
        """
        op = self.xcall("get-ntfsinfo %s" % part)
        rx = re.compile(r"^[^0-9]* ([0-9]+) ")
        lines = op.splitlines()
        try:
            self.ntfs_cluster_size = int(rx.search(lines[0]).group(1))
            cvs = int(rx.search(lines[0]).group(1))
            cds = int(rx.search(lines[0]).group(1))
            srp = int(rx.search(lines[0]).group(1))
        except:
            plog("get-ntfsinfo failed")
            return None
        return (self.ntfs_cluster_size, cvs, cds, srp)

    def getNTFSmin(self, part):
        """Get the minimum size in bytes for shrinking the given NTFS
        partition.
        """
        return self.getNTFSinfo(part)[3]

    def doNTFSshrink(self, device, partnum, size, partstart, diskinfo):
        """Shrink selected NTFS partition. First the file-system is shrunk,
        then the partition containing it. size and partstart are in sectors.
        """
        dev = "%s%d" % (device, partnum)
        ## This rounding to whole clusters may well not be necessary
        #clus = int(s * 1e6) / self.ntfs_cluster_size
        #newsize = clus * self.ntfs_cluster_size
        newsize = size * diskinfo[3]

        # First a test run
        info = PopupInfo(_("Test run ..."), _("Shrink NTFS partition"))
        res = self.xcall("ntfs-testrun %s %s" % (dev, newsize))
        info.drop()
        if res:
            return res

        # Now the real thing, resize the file-system
        info = dialogs.PopupInfo(_("This is for real, shrinking file-system ..."),
                _("Shrink NTFS partition"))
        res = self.xcall("ntfs-resize %s %s" % (dev, newsize))

        info.drop()
        if res:
            return res

        # Now resize the actual partition, so that it ends at a cylinder
        # boundary after the end of the ntfs filesystem.
        cylsize = diskinfo[2]
        end = int((partstart + size + 2*cylsize) / cylsize) * cylsize
        info = dialogs.PopupInfo(_("Resizing partition ..."),
                _("Shrink NTFS partition"))
        res = self.xcall("part-resize %s %d %d" %
                (device, partnum, end - partstart))
        info.drop()
        if res:
            return res

        # And finally expand the ntfs file-system into the new partition
        info = dialogs.PopupInfo(_("Fitting file-system to new partition ..."),
                _("Shrink NTFS partition"))
        res = self.xcall("ntfs-growfit %s" % dev)
        info.drop()
        return res


    def gparted_available(self):
        """Return '' if gparted is available.
        """
        return self.xcall("gparted-available", "-Y")


    def gparted(self):
        return self.xcall("gparted-run", "-Y")


    def cfdisk(self, dev):
        if self.host:
            cmd = "ssh -t root@%s cfdisk %s" % (self.host, dev)
        else:
            cmd = "cfdisk %s" % dev
        self.terminal(cmd)


    def rmpart(self, dev, partno):
        """Remove the given partition  (device + partition number).
        """
        return self.xcall("rmpart %s %d" % (dev, partno))


    def rmparts(self, dev, partno):
        """Remove all partitions on the given device starting from the
        given partition number.
        """
        parts = self.xcall("listparts %s" % dev).splitlines()
        i = len(parts)
        while (i > 0):
            i -= 1
            p = int(parts[i])
            if (p >= partno):
                op = self.xcall("rmpart %s %d" % (dev, p))
                if op: return op
        return ""


    def makepart(self, dev, partnum, startcyl, endcyl, swap=False):
        """Make a partition on the given device with the given start and
        end points. By default a 'linux' partition will be created, but
        a 'swap' partition can also be requested. partnum can be 1-4, in
        which case, a primary partition will be created/changed, 0, in
        which case an extended partition will be created as fourth
        partition, or -1, in which case a logical partition will be
        created.
        """
        # Note that separate calls are used for logical and
        # primary/extended partitions. This is because I could see no
        # way of making parted add a primary partition with a given number
        # and no way of creating a logical partition with sfdisk ...
        if (partnum == 0):
            self.xcall("newpart2 %s %d %d %d %s" % (dev, 4,
                    startcyl, endcyl, "05"))

        elif (partnum == -1):
            if swap:
                ptype = "linux-swap"
            else:
                ptype = "ext2"
            return self.xcall("newpart %s %d %d %s %s" % (dev,
                    startcyl, endcyl, ptype, "logical"))

        else:
            if swap:
                ptype = "82"
            else:
                ptype = "83"
            self.xcall("newpart2 %s %d %d %d %s" % (dev, partnum,
                    startcyl, endcyl, ptype))


    def getlinuxparts(self, dev):
        """Return a list of partitions on the given device with linux
        partition code (83).
        """
        return self.xcall("linuxparts %s" % dev).split()


    def getActiveSwaps(self):
        """Discover active swap partitions. Return list
        of pairs: (device, size(GB)).
        """
        output = self.xcall("get-active-swaps")
        swaps = []
        for l in output.splitlines():
            ls = l.split()
            swaps.append((ls[0], float(ls[1]) * 1024 / 1e9))
        return swaps


    def getAllSwaps(self):
        """Discover swap partitions, whether active or not. Return list
        of pairs: (device, size(GB)).
        """
        # I might want to add support for LVM/RAID?
        output = self.xcall("get-all-swaps")
        swaps = []
        for l in output.splitlines():
            ls = l.split()
            swaps.append((ls[0], float(ls[1]) * 1024 / 1e9))
        return swaps


    def swapFormat(self, p, c):
        # If the partition alread has a UUID, keep it
        uuid = self.getUUID(p).strip()
        if uuid:
            c += (" -U '%s'" % uuid)
        return self.xcall("swap-format %s %s" % (c, p))


    def partFormat(self, part, format, options):
        return self.xcall("part-format %s %s %s" % (part, format, options))


    def checkEmpty(self, mp):
        if self.xcall("check-mount %s" % mp):
            return self.showWarning(_("The partition mounted at %s is not"
                    " empty. This could have bad consequences if you"
                    " attempt to install to it. Please reconsider.\n\n"
                    " Do you still want to install to it?") % mp)
        return True


    def guess_size(self, d='/'):
        """Get some estimate of the size of the given directory d, in MiB.
        """
        return int(self.xcall("guess-size %s" % d))


    def lsdir(self, d):
        """Get a list of items in the given directory ('ls').
        """
        return self.xcall("lsdir %s" % d).split()


    def copyover(self, dir, cb):
        self.xcall("copydir %s" % dir, callback=cb)


    def install_tidy(self):
        """Complete the copy part of the installation, creating missing
        items, etc.
        """
        self.xcall("larch-tidy")


    def get_size(self, log=False):
        """Get some estimate of the current size of the system being
        installed.
        Returns a value in MiB.
        """
        return int(self.xcall("installed-size", log=log))


    def mount(self):
        """The order is important in some cases, so when building the list
        care must be taken that inner mounts (e.g. '/home') are placed
        after their containing mounts (e.g. '/') in the list.
        """
        return self.remount(True)


    def getumounts(self):
        """Each entry is a list of partition, mount-point and mount-flags
        """
        return [m.split(':') for m in self.get_config('mounts').splitlines()]


    def remount(self, check=False):
        """This mounts the partitions used by the new system using the
        list in the 'mounts' config file.
        """
        mplist = self.getumounts()
        for d, m, f in mplist:
            result = self.xcall("do-mount %s %s" % (d, m))
            if result:
                return None
            # Check that there are no files on this partition. The warning
            # can be ignored however.
            if check and not self.checkEmpty(m):
                return None
        return mplist


    def unmount(self):
        """To unmount the partitions mounted by the installer.
        """
        mlist = self.getumounts()
        mlist.reverse()
        for d, m, f in mlist:
            result = self.xcall("do-unmount %s" % m)
            if result:
                return False
        return True


    def mkinitcpio(self):
        self.xcall("do-mkinitcpio")


    def getswaps(self):
        """Retrieve swap partition list from config file 'swaps'
        """
        # Swaps ([device, format, include])
        slist = []
        swaps = self.get_config("swaps", False)
        if swaps:
            for s in swaps.splitlines():
                slist.append(s.split(':'))
        return slist


    def getUUID(self, part):
        return self.xcall("get-blkinfo UUID %s" % part).strip()


    def fstab(self):
        """Build a suitable /etc/fstab for the newly installed system.
        """
        fstab = ("# fstab generated by larchin\n"
                "#<file system>   <dir>       <type>      <options>"
                        "    <dump> <pass>\n")

        mainmounts = []
        mmounts = []
        xmounts = []
        mplist = self.getumounts()
        for d, m, f in mplist:
            mainmounts.append(d)
            opt = 'defaults'
            if (m == '/'):
                pas = '1'
            else:
                pas = '2'
            sysm = True
            if ('A' in f):
                opt += ',noatime'
            if ('D' in f):
                opt += ',nodiratime'
            if ('M' in f):
                opt += ',noauto'
                pas = '0'
                sysm = False

            # Read format? or just use 'auto'?
            fstype = self.xcall("get-blkinfo TYPE %s" % d).strip() or "auto"
            if self.use_uuid:
                u = self.getUUID(d)
                s = ("/dev/disk/by-uuid/%s %-12s %-8s %s 0     %s\n" %
                        (u, m, fstype, opt, pas))
            else:
                s = "%-15s %-12s %-8s %s 0     %s\n" % (d, m, fstype, opt, pas)
            if sysm:
                mmounts.append((m, s))
            else:
                xmounts.append((m, s))

        mmounts.sort()
        for m, s in mmounts:
            fstab += s

        fstab += ("\nnone            /dev/pts    devpts      defaults"
                        "        0     0\n"
                "none            /dev/shm    tmpfs       defaults"
                        "        0     0\n\n")

        fstab += "# Swaps\n"
        for p, f, i in self.getswaps():
            if i:
                if self.use_uuid_swap:
                    p = ("/dev/disk/by-uuid/" + self.getUUID(p))
                fstab += ("%s swap       swap   defaults        0     0\n"
                        % p)

        if xmounts:
            fstab += "#\n Other partitions\n"
            xmounts.sort()
            for m, s in xmounts:
                fstab += s

        fstab += "\n#Optical drives\n"
        for p in self.xcall("get-cd").splitlines():
            fstab += ("#/dev/%-6s /mnt/cd_%-4s auto"
                    "   user,noauto,exec,unhide 0     0\n" % (p, p))

        # Add other partitions to /mnt if not already catered for.
        # One shouldn't assume the existing device info is up to date.

        dl = []
        for devi in self.xcall("get-usableparts").splitlines():
            devi = devi.split()
            dev = "/dev/" + devi[0]
            if (dev not in mainmounts):
                dl.append(devi)
        if dl:
            fstab += "\n#Additional partitions\n"
            for devi in dl:
                if (devi[1] == '+'):
                    # removable
                    pass
                else:
                    fstype = devi[2].strip('"') or "auto"
                    if self.use_uuid:
                        u = self.getUUID("/dev/%s" % devi[0])
                        s = ("#/dev/disk/by-uuid/%s /mnt/%-7s %s    "
                                "user,noauto,noatime"
                                " 0     0\n" % (u, devi[0], fstype))

                    else:
                        s = ("#/dev/%-7s /mnt/%-7s %s    user,noauto,noatime"
                                " 0     0\n" % (devi[0], devi[0], fstype))

                    fstab += s

        dl = []
        for dev in self.xcall("get-lvm").splitlines():
            devm = "/dev/mapper/" + dev
            if (devm not in mainmounts):
                dl.append(dev)
        if dl:
            fstab += "\n#LVM partitions\n"
            for p in dl:
                fstab += ("#/dev/mapper/%-6s /mnt/lvm_%-4s auto"
                    "   user,noauto,noatime 0     0\n" % (p, p))

        fstab += ("\n# You may also want to add lines for removable devices,\n"
                "# though it is recommended to let HAL deal with these.\n"
                "# You will also need to create the mount point in /mnt.\n"
                "# For example:\n"
                "#/dev/sdb1 /mnt/usb    auto    user,noauto,noatime 0    0\n")

        fw = open("/tmp/larchin/fstab", "w")
        fw.write(fstab)
        fw.close()
        self.xsendfile("/tmp/larchin/fstab", "/tmp/install/etc/fstab")


    def set_devicemap(self):
        """Generate a (temporary) device.map file on the target and read
        its contents to a list of pairs in self.device_map.
        It also scans all partitions for menu.lst files, which are
        then stored as (device, path) pairs.
        """
        if self.remount():
            # Filter out new system '/' and '/boot'
            bar = []
            mplist = self.getumounts()
            for d, m, f in mplist:
                if (m == '/') or (m == '/boot'):
                    bar.append(d)

            self.device_map = []
            self.menulst = []
            for line in self.xcall("mkdevicemap").splitlines():
                spl = line.split()
                if (spl[0].startswith('(')):
                    self.device_map.append(spl)
                elif (spl[0] == '+++'):
                    d = self.grubdevice(spl[2])
                    if d not in bar:
                        self.menulst.append((d, spl[1]))
            ok = self.unmount() and (self.device_map != [])
            return ok
        return False


    def grubdevice(self, device):
        """Convert from a grub drive name to a linux drive name, or vice
        versa. Uses the information previously gathered by set_devicemap().
        This works for drives and partitions in both directions.
        """
        if device.startswith('('):
            d = device.split(',')
            if (len(d) == 1):
                part = ''
            else:
                part = str(int(d[1].rstrip(')')) + 1)
                d = d[0] + ')'
            for a, b in self.device_map:
                if (a == d):
                    return (b + part)
        else:
            d  = device.rstrip('0123456789')
            if (d == device):
                part = ')'
            else:
                part = ',%d)' % (int(device[len(d):]) - 1)
            for a, b in self.device_map:
                if (b == d):
                    return a.replace(')', part)
        return None


    def getbootinfo(self):
        """Retrieves kernel file name and a list of initramfs files from
        the boot directory of the newly installed system.
        """
        self.remount()
        kernel = None
        inits = []
        for line in self.xcall("get-bootinfo").splitlines():
            if line.startswith('+++'):
                kernel = line.split()[1]
            else:
                inits.append(line)
        self.unmount()
        if not inits:
            self.error = _("No initramfs found")
            assert False
        if not kernel:
            self.error = _("GRUB problem:\n") + inits[0]
            assert False
        return (kernel, inits)


    def readmenulst(self, dev, path):
        return self.xcall("readmenulst %s %s" % (dev, path))


    def setup_grub(self, dev, path, text):
        fh = open("/tmp/larchin/menulst", "w")
        fh.write(text)
        fh.close()
        if dev:
            self.remount()
            self.xcall("grubinstall %s" % dev)
            self.xsendfile("/tmp/larchin/menulst",
                    "/tmp/install/boot/grub/menu.lst")
            self.unmount()

        else:
            # Just replace the appropriate menu.lst
            d, p = path.split(':')
            self.xcall("mount1 %s" % d)
            self.xsendfile("/tmp/larchin/menulst", "/tmp/mnt%s" % p)
            self.xcall("unmount1")


    def set_rootpw(self, pw):
        if (pw == ''):
            # Passwordless login
            pwcrypt = ''
        else:
            # Normal MD5 password
            salt = '$1$'
            for i in range(8):
                salt += random.choice("./0123456789abcdefghijklmnopqrstuvwxyz"
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            pwcrypt = crypt.crypt(pw, salt)

        self.remount()
        op = self.xcall("setpw root '%s'" % pwcrypt)
        self.unmount()
        if op:
            self.error= _("Couldn't set root password:\n") + op
            assert False
