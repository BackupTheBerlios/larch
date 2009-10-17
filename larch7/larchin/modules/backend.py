# backend.py
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

from subprocess import Popen, PIPE, STDOUT
import os, threading
import re

# Mount point for the installation root partition
IBASE = "/tmp/install"

class Backend:
    """Interaction with the machine is dealt with via the interface provided
    in this class, in general by means of running small shell scripts which
    are in the larchin-syscalls package and can be on a separate machine
    from that on which larchin is running.
    For running commands on a separate machine it is necessary to use ssh
    with public-key authentication, so that no password is required.
    """
    def __init__(self, host):
        self.host = host

        self.process = None
        self.process_lock = threading.Lock()

        # Keep a record of mounts
        self.mounts = []


#TODO: Maybe this should be done outside of __init__
#        if (self.xcall("init") != ""):
#            fatal_error(_("Couldn't initialize installation system"))


    #************ Methods for calling bash scripts

#Not yet used
    def xsendfile(self, path, dest):
        """Copy the given file (path) to dest on the target.
        """
        plog("COPY FILE: %s (host) to %s (target)" % (path, dest))
        if self.host:
            self.process = Popen("scp -q %s root@%s:%s" %
                    (path, self.host, dest), shell=True,
                    stdout=PIPE, stderr=STDOUT)
            plog(self.process.communicate()[0])
            self.process = None
        else:
            shutil.copyfile(path, dest)
        assert self.interrupt == None


    def _xcall_local(self, cmd):
        """Call a function on the same machine.
        """
        if os.path.isdir(base_dir + "/syscalls"):
            basePath = base_dir
        else:
            basePath = os.path.dirname(base_dir) + "/larchin-syscalls"
        xcmd = ("%s/syscalls/0call %s" % (basePath, cmd))
        return Popen(xcmd, shell=True, stdout=PIPE, stderr=STDOUT, bufsize=1)


    def _xcall_net(self, cmd, opt=""):
        """Call a function on another machine.
        Public key authentication must be already set up so that no passsword
        is required.
        """
        xcmd = ("ssh %s root@%s /opt/larchin/syscalls/0call %s" %
                (opt, self.host, cmd))
        return Popen(xcmd, shell=True, stdout=PIPE, stderr=STDOUT, bufsize=1)


#Not yet used
    def terminal(self, cmd):
        """Run a command in a terminal. The environment variable 'XTERM' is
        recognized, otherwise one will be chosen from a list.
        """
        term = os.environ.get("XTERM", "")
        if (os.system("which %s &>/dev/null" % term) != 0):
            for term in ("terminal", "konsole", "xterm", "rxvt", "urxvt"):
                if (os.system("which %s &>/dev/null" % term) != 0):
                    term = None
                else:
                    break

        assert term, _("No terminal emulator found")
        if (term == "terminal"):
            term += " -x "
        else:
            term += " -e "

        plog("TERMINAL: %s" % cmd)
        self.process = Popen(term + cmd, shell=True)
        plog(self.process.communicate()[0])
        self.process = None
        assert self.interrupt == None


    def xlist(self, cmd, opt="", xlog=None):
        self.process_lock.acquire()
        if self.process:
            bug("Attempt to start second shell process")
        self.interrupt = 0
        if self.host:
            self.process = self._xcall_net(cmd, opt)
        else:
            self.process = self._xcall_local(cmd)
        self.process_lock.release()

        logger.addLine("XCALL: %s" % cmd)
        self.oplines = []
        while True:
            line = self.process.stdout.readline()
            if not line: break
            line = line.rstrip()
            if xlog:
                xlog(line)
            else:
                self.oplines.append(line)
                logger.addLine(line)
        logger.addLine("END-XCALL")
        self.process.wait()
        rc = self.process.returncode
        lines = self.oplines

        self.process_lock.acquire()
        command.breakin = self.interrupt
        self.process = None
        self.process_lock.release()
        assert command.breakin == 0
        return (rc == 0, lines)


    def xcheck(self, cmd, opt="", xlog=None, onfail=None):
        ok, l = self.xlist(cmd, opt, xlog)
        if not ok:
            run_error(onfail if onfail else
                    (_("Operation failed:\n  %s") % cmd))
        return ok


    def killprocess(self):
        self.process_lock.acquire()
        if self.process:
            if self.host:
                self._xcall_net("0kill").wait()
            else:
                self._xcall_local("0kill").wait()
            self.interrupt = 1
        self.process_lock.release()


########################################################################
# Interface functions

    def run_mount_devprocsys(self, fn, *args):
        ok = True
        dirs = []
        for d in ("/dev", "/proc", "/sys"):
            mpb = IBASE + d
            if self.xcheck("do-mount --bind %s %s" % (d, mpb),
                    onfail=_("Couldn't bind-mount %s at %s") % (d, mpb)):
                self.mounts.append(mpb)
                dirs.append(mpb)
            else:
                ok = False
        if ok:
            ok = fn(*args)
        return self.unmount(dirs) and ok


    def imount(self, dev, mp):
        mpreal = IBASE if mp == "/" else IBASE + mp
        if self.xcheck("do-imount %s %s %s" % (IBASE, dev, mp),
                onfail=_("Couldn't mount %s at %s") % (dev, mpreal)):
            self.mounts.append(mpreal)
            return True
        return False


    def imounts(self, mlist):
        self.mountlist = mlist
        for d, m in mlist:
            if not self.imount(d, m):
                return False
        return True


    def unmount(self, dst=None):
        if dst == None:
            mounts = list(self.mounts)
        elif type(dst) in (list, tuple):
            mounts = list(dst)
        else:
            mounts = [dst]

        r = True
        mounts.reverse()
        for m in mounts:
            if self.xcheck("do-unmount %s" % m,
                    onfail=_("Couldn't unmount %s") % m):
                self.mounts.remove(m)
            else:
                r = False
        return r


    def format(self, dev, fmt):
        return self.xcheck("part-format %s %s" % (dev, fmt),
                onfail=_("Formatting of %s failed") % dev)


    def rmparts(self, dev, frompartno):
        """Remove all partitions on the given device starting from the
        given partition number.
        """
        parts = DiskInfo(dev).parts
        parts.reverse()
        for p in parts:
            pn = int(p[0][len(dev):])
            if (pn >= frompartno) and not self.rmpart(dev, pn):
                return False
        return True


    def rmpart(self, dev, partno):
        """Remove the given partition.
        """
        return self.xcheck("rmpart %s %d" % (dev, partno),
                onfail=_("Couldn't remove partition %s%d") % (dev, partno))


    def newpart(self, device, primary, ncyls, swap=False):
        """Create a partition on the given device.
        The partition will be created immediately after the last occupied
        cylinder.
        Only Linux and Linux Swap partition types are supported.
        Return the partition number of the created partition.
        """
        # This is a simple partitioning tool, which only supports
        # adding partitions sequentially, with all primary partitions
        # being before the extended partition, so once a logical
        # partition has been added, it is not possible to add further
        # primary ones.
        di = DiskInfo(device)
        pmax = 0            # Record highest partition number
        lim = -1            # Used for seeking last used cylinder
        exp = 0             # Number of extended partition
        ex0, ex1 = 0, -1    # Extended partition start and end
        log0, log1 = 0, -1  # Start and end of area used by logical partitions
        for p in di.parts:
            pn = int(p[0][len(device):])
            scyl, ecyl = p[1:3]
            if pn <= 4:
                if exp:
                    run_error(_("Not supported: primary partition (%s%d)\n"
                            "has higher partition number than extended "
                            "partition") % (device, pn))
                    return ""
            if scyl <= lim:
                run_error(_("Partitions must be ordered on the device.\n"
                        "%s%d is out of order.") % (device, pn))
                return ""
            if p[3] in ("5", "f"):
                # extended
                exp = pn
                ex0, ex1 = scyl, ecyl
                continue
            pmax = pn
            lim = ecyl

        startcyl = lim + 1
        endcyl = lim + ncyls
        if endcyl >= di.drvcyls:
            run_error(_("Too little space at end of drive for new partition"))
            return ""
        if exp and (pmax <= 4):
            # Remove the extended partition, which is empty anyway
            if not self.rmpart(device, exp):
                return ""
            pmax = exp - 1
        if primary:
            if pmax >= 4:
                run_error(_("Cannot add primary partition to %s") % device)
                return ""
            t = "primary"
        else:
            t = "logical"
            if pmax > 4:
                # resize extended partition
                if not self.xcheck("resize %d %d %d" % (device, exp,
                                ex0, endcyl),
                        onfail=_("Couldn't resize extended partition %s%d")
                                % (device, exp)):
                    return False
            else:
                # create extended partition
                if not self.xcheck("newpart %s %d %d extended" % (device,
                                startcyl, endcyl),
                        onfail=_("Couldn't create extended partition on %s")
                                % device):
                    return False
            if pmax < 4:
                pmax = 4

        if self.xcheck("newpart %s %d %d %s %s" % (device, startcyl, endcyl,
                t, "linux-swap" if swap else "ext2")):
            return "%s%d" % (device, pmax + 1)
        else:
            run_error(_("Couldn't add new partition to %s") % device)
            return ""


    def mkswap(self, partition, check):
        """Format the given swap partition. I don't know what happens if
        check is True and bad blocks are found, so including it is a bit
        pointless, but maybe I'll find out one day ...
        """
        return self.xlist("swap-format " + ("-c " if check else "")
                + partition)[0]


    def copy_system(self, logfun):
        if ("i" not in dbg_flags) and not self.xcheck("copy-system %s"
                % IBASE, xlog=logfun,
                        onfail=_("Copying of system data failed")):
            return False
        return self.xcheck("fix-system1 %s" % IBASE,
                onfail=_("Initial installed system tweaks failed (see log)"))


    def delivify(self):
        return self.xcheck("fix-system2 %s" % IBASE,
                onfail=_("Failure while removing live-system modifications"
                        " (see log)"))


    def initramfs(self):
        return self.run_mount_devprocsys(self._initramfs)

    def _initramfs(self):
        return self.xcheck("do-mkinitcpio %s" % IBASE,
                onfail=_("Problem building initramfs (see log)"))



class DiskInfo:
    """Get info on drive and partitions.

    It uses 'fdisk -l' to get the information about the drive.
    The output of the call is parsed to extract useful information.
    Of course the instance must be discarded as soon as changes are
    made to the device.
    """
    def __init__(self, device):
        self.device = device
        info = backend.xlist("fdisk-l " + device)[1]
        while not info[0].startswith("Disk"):
            del(info[0])
        self.driveinfo = info[0]

        # get the drive size in cylinders
        self.drvcyls = int(re.search(r",[^,]+,[ ]*([0-9]+)", info[1]).group(1))

        # get cylinder size in sectors and sector size in bytes
        ds = re.search(r"([0-9]+)[ ]*\*[ ]*([0-9]+)", info[2])
        self.cylsects = int(ds.group(1))
        self.secbytes = int(ds.group(2))

        # Get partition info
        self.parts = []
        for pline in info[5:]:
            if pline.startswith("/dev/"):
                items = pline.replace("*", " ").split(None, 5)
                self.parts.append((items[0], int(items[1])-1, int(items[2])-1,
                        items[4], items[5]))
                # That's (device, startcyl, endcyl, type-id, type-name)
                # fdisk counts cylinders from 1, but sfdisk and parted
                # count from 0, so adjust the values here to start from 0.

    def drivesize_str(self):
        """Get the drive size as a string.
        """
        return re.search(r"%s:([^,]+)" % self.device, self.driveinfo).group(1)

    def cyl2B(self):
        """Return the number of bytes per cylinder.
        """
        return self.cylsects * self.secbytes

    def partsizeMB(self, device):
        for p in self.parts:
            if p[0] == device:
                return ((p[2] - p[1] + 1) * self.cyl2B() + 5*10**5) / 10**6
        return None

    def get_freecyls(self):
        """Assume the free space is at the end of the drive!
        Return the number of free cylinders at the end of the device.
        """
        lastcyl = 0
        for p in self.parts:
            if p[2] > lastcyl:
                lastcyl = p[2]
        return self.drvcyls - lastcyl - 1   # cylinder numbers start at 0


class PartInfo:
    """Get information on a specific partition.
    """
    def __init__(self, device):
        self.device = device

    def getfstype(self):
        ok, l = backend.xlist("get-blkinfo TYPE %s" % self.device)
        if ok and l:
            return l[0]
        else:
            return ""

    def sizeGB(self):
        l = backend.xlist("partsizes %s" % self.device)[1]
        return float(l[0].split()[1]) / 1e9
