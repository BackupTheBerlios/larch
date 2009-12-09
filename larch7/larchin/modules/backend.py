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
# 2009.12.09

#from subprocess import Popen, PIPE, STDOUT
import os, shutil, threading
import pexpect
from Queue import Queue
import re, json
import crypt, random

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
        # Lock to protect starting and ending of processes
        self.process_lock = threading.Lock()
        # Event to wait for backend shutdown (initially unset, blocking a wait)
        self.process_event = threading.Event()
        self.fgid = None
        self.idcount = 0
        self.queues = {}

        # Keep a record of mounts
        self.mounts = []

        # Keep a record of the (estimated) size of the installation
        self.totalMB = 0


    def start(self):
        """Because it may be necessary to fetch the root password, the gui
        must be running when this is entered.
        """
        if self.process:
            return True
        if self.host:
            cmd = "ssh -Y root@%s" % self.host
        else:
            cmd = "su -c"
        cmd +=  " 'echo _GO_ && larchin-0call'"
        # Run the command as root with pexpect.
        # Return True if it succeeded, else False.
        p = pexpect.spawn(cmd, timeout=None)
        e = p.expect(["_GO_.*\n", pexpect.TIMEOUT, "Password:"], 5)
        while e != 0:
            if e == 2:
                ok, pw = ui.textLineDialog(_("Please enter root password"),
                        "larchin: root pw", pw=True)
                if not ok:
                    run_error( _("No root password, cancelling run"))
                    return False

                p.sendline(pw.strip())
                e = p.expect(["_GO_.*\n", pexpect.TIMEOUT, pexpect.EOF], 5)
            else:
                run_error(_("Couldn't start larchin-0call"))
                return False
        self.process = p
        p.setecho(False)

        # Start a thread to read input from 0call.
        command.simple_thread(self.read0call)
        # Perform initialization of the installation system
        ok, textlines = self.xlist("init")
        if not ok:
            run_error(_("Couldn't initialize installation system:\n\n%s")
                    % "\n".join(textlines))
        return ok


    def read0call(self):
        line0 = ""
        while True:
            ch = self.process.read(1)
            if not ch:
                if not line0:
                    break
            elif ch == "\n":
                continue
            elif ch != "\r":
                line0 += ch
                continue
            line = line0.strip()
            line0 = ""
#            if not line:
#                continue
            if line[0] == "/":
                plog(line)

                if line[1] =="/":
                    break

                else:
                    id, rc = line[1:].split(":")
                    if id == "kill":
                        self.kill_rc = rc
                        self.kill_event.set()
                    elif id == "file":
                        self.file_rc = rc
                        self.file_event.set()
                    else:
                        self.queues[int(id)].put("/" + rc)

            elif line[0] == ">":
                id, rest = line[1:].split(":", 1)
                if id[0] != "-":
                    plog(line)
                self.queues[int(id)].put(">" + rest)

            elif line[0] == "!":
                # This is just a message from the backend, for logging
                plog(line)

            else:
                plog(line)
                plog("BUG: ^^^ Unexpected line from 0call")

        # 0call is exiting
        self.process = None
        self.process_event.set()


    def call0(self, cmd, args, fg=True, xlog=None):
        self.process_lock.acquire()
        try:
            self.idcount += 1
            id = self.idcount
            if xlog:
                # There must be some way for the receiver to know that
                # the normal output of this process is not to go to plog.
                id = -id
            if fg:
                if self.fgid:
                    bug("Attempt to start second foreground syscall")
                    return  # Actually, bug should terminate the run
                self.fgid = id
                self.interrupt = 0
            self.queues[id] = Queue()
            self.process.sendline("call %d %s %s" %
                    (id, cmd, json.dumps(args)))
        finally:
            self.process_lock.release()
        return id


    def killprocess(self, terminate=False):
        if not self.process:
            return False
        self.process_lock.acquire()
        self.kill_event = threading.Event()
        self.process.sendline("kill")
        self.kill_event.wait()
        if self.fgid:
            self.interrupt = 1
        ret = self.kill_rc == "0"
        self.process_lock.release()
        return ret


    def tidy(self, terminate):
        if self.process:
            self.unmount()
            if terminate:
                self.process.sendline("/")
                self.process_event.wait()


    def readline(self, id):
        r = self.queues[id].get()
        self.queues[id].task_done()
        if r[0] == "/":
            del(self.queues[id])
        return r


    def xwritefile(self, contents, dest):
        """Write the contents to the given file (dest) on the target,
        within the installation mount.
        """
        plog("Write FILE: %s (target)" % dest)
        self.process_lock.acquire()
        self.file_event = threading.Event()
        self.process.sendline("file %s" %
                json.dumps((IBASE, dest, contents)))
        self.file_event.wait()
        ret = self.file_rc == "0"
        self.process_lock.release()
        return ret


    def xlist(self, cmd, *args, **kargs):
        plog("XCALL: %s %s" % (cmd, repr(args)))
        xlog = kargs.get("xlog")
        id = self.call0(cmd, args, xlog=xlog)
        lines = []
        while True:
            line = self.queues[id].get()
            rest = line[1:]
            if line[0] == "/": break
            if xlog:
                xlog(rest)
            else:
                lines.append(rest)
        plog("END-XCALL")
        self.process_lock.acquire()
        if self.interrupt != 0:
            ui.setInterrupt()
        interrupt = self.interrupt
        self.fgid = None
        self.process_lock.release()
        assert interrupt == 0
        return (rest == "0", lines)


    def xcheck(self, cmd, *args, **kargs):
        ok, l = self.xlist(cmd, *args, **kargs)
        if not ok:
            onfail = kargs.get("onfail")
            run_error(onfail if onfail else
                    (_("Operation failed:\n  %s") % cmd))
        return ok


    def bgproc(self, cmd, args=[], tidy=None):
        plog("CALL: %s %s" % (cmd, repr(args)))
        id = self.call0(cmd, args, fg=False)
        res = ""
        while True:
            line = self.readline(id)
            if line[0] == "/": break
            res += line[1:] + "\n"
        if tidy:
            tidy(res)
        plog("CALL-END: %s" % cmd)


########################################################################
# Interface functions

    def memsize(self):
        """Return the size of the system memory, in bytes.
        """
        return self.xlist("get-memsize")[1][0] * 1024


    def get_medium_size_estimate(self):
        """Base the estimate on the sizes of system.sqf, mods.sqf
        and overlay.tar.lzo. The result is in MB.
        """
        size = 10   # Start with 10 MB
        for f in ("system.sqf", "mods.sqf", "overlay.tar.lzo"):
            sb = self.filesize("/.livesys/medium/larch/" + f)
            size += (sb + 5*10**5) / 10**6
        return size


    def filesize(self, path):
        ok, bytes = self.xlist("filesize", path)
        if not ok:
            run_error(_("Couldn't stat file '%s'") % path)
            return 0
        return int(bytes[0])


    def available(self, app):
        """Test the availability of the given application (whether the
        given name is executable, using 'which') on the installation
        system.
        """
        return self.xlist("testfor", app)[0]


    def get_devices(self):
        """Return a list of discovered devices, for each a list of strings:
            [device, size, device type]
        This is intended for information only, not for calculation with the
        size, which will also include a unit.
        """
        # If devices are added (by writing partition tables to blank devices)
        # the detection process should be repeated, so a loop is used
        rex = re.compile(r"Error: *(/dev/[^:]*): *unrec[^:]*label")
        for round in (0, 1):
            newdev = False
            # Note that if one of the devices has mounted partitions it
            # won't be available for automatic partitioning, and should
            # thus not be included in the list used for automatic installation
            lines = []
            for line in self.xlist("get-devices")[1]:
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
                        if self.xlist("make-parttable", dev)[0]:
                            newdev = True
                        else:
                            run_error(_("Couldn't create partition table on %s" % dev))
                else:
                    lines.append([i.strip() for i in line.split(":")])

            if not newdev: break
        return lines


    def get_mounts(self):
        """Return a list of mounted partitions.
        """
        return [m.split()[0] for m in self.xlist("get-mounts")[1]]


    def get_partfstype(self, part):
        """Use blkid to get fstype of the given partition.
        """
        t = self.xlist("get-blkinfo", part, "TYPE")
        return t[1][0] if t[0] and (len(t[1]) != 0) else ""


    def file_rw(self, dev, path, text=None):
        """Reads or writes the file at 'path' on device 'dev'.
        Mounts the given device at IBASE (which means this method
        cannot be used while the system being installed is mounted).
        If the device is already mounted use mount --bind.
        If text!=None it is a write operation, and if the device is
        already mounted, but ro, an attempt will be made to remount it
        rw for the duration of the operation.
        On writing the result can be None or True, but on reading the
        result is more complicated. None indicates something went wrong
        with the mounting, otherwise the pair (ok, linelist) is returned,
        in which linelist is the file contents if ok is True, otherwise
        whatever output the low level command provides.
        """
        rorw = None     # Flag to indicate remount rw
        bind = False    # Flag to indicate mount --bind
        for m in self.xlist("get-mounts")[1]:
            md, mp = m.split()
            if md == dev:
                if (text != None) and self.xlist("testromount", mp)[0]:
                    # Writing to ro mount, attempt to remount rw
                    if not self.remount(mp, "rw"):
                        return None
                    rorw = mp
                if not self.mountbind(mp):
                    if rorw:
                        self.remount(mp, "ro")
                    return None
                bind = True
                break
        if (not bind) and not self.imount(dev, "/"):
            return None
        if (text != None):
            # Write file
            ok = self.xwritefile(text, path)
            ok = self.unmount() and ok
            if rorw:
                ok = self.remount(rorw, "ro") and ok
            return True if ok else None
        else:
            # Read file
            ok, lines = self.xlist("readfile", IBASE + path)
            if not self.unmount():
                return None
            return (ok, lines)


    def remount(self, mp, opt):
        return self.xcheck("do-mount", "-o", "remount," + opt, mp,
                onfail=_("Couldn't remount '%s' %s") % (mp, opt))


    def mountbind(self, dir, mp=""):
        mpb = IBASE + mp
        if self.xcheck("do-mount", "--bind", dir, mpb,
                onfail=_("Couldn't bind-mount %s at %s") % (dir, mpb)):
            self.mounts.append(mpb)
            return True
        return False


    def run_mount_devprocsys(self, fn, *args):
        ok = True
        dirs = []
        for d in ("/dev", "/proc", "/sys"):
            if self.mountbind(d, d):
                dirs.append(IBASE + d)
            else:
                ok = False
                break
        if ok:
            ok = fn(*args)
        return self.unmount(dirs) and ok


    def mount(self):
        if self.partition_list[0][0] != "/":
            config_error(_("No root partition ('/') found"))
            return False
        mlist = []
        for part in self.partition_list:
            mp, dev = part[0], part[1]
            if mp.startswith("/"):
                ui.progressPopup.add(_("Mounting %s at %s") % (dev, mp))
                mlist.append((dev, mp))
        return self.imounts(mlist)


    def imounts(self, mlist):
        self.mountlist = mlist
        for d, m in mlist:
            if not self.imount(d, m):
                return False
        return True


    def imount(self, dev, mp):
        mpreal = IBASE if mp == "/" else IBASE + mp
        if self.xcheck("do-imount", IBASE, dev, mp,
                onfail=_("Couldn't mount %s at %s") % (dev, mpreal)):
            self.mounts.append(mpreal)
            return True
        return False


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
            if self.xcheck("do-unmount", m,
                    onfail=_("Couldn't unmount %s") % m):
                self.mounts.remove(m)
            else:
                r = False
        return r


    def format(self, dev, fmt):
        return self.xcheck("part-format", dev, fmt,
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
        return self.xcheck("rmpart", dev, str(partno),
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
                if not self.xcheck("resizepart", device, str(exp),
                                str(ex0), str(endcyl),
                        onfail=_("Couldn't resize extended partition %s%d")
                                % (device, exp)):
                    return False
            else:
                # create extended partition
                if not self.xcheck("newpart", device,
                                str(startcyl), str(endcyl), "extended",
                        onfail=_("Couldn't create extended partition on %s")
                                % device):
                    return False
            if pmax < 4:
                pmax = 4

        if self.xcheck("newpart", device, str(startcyl), str(endcyl),
                t, "linux-swap" if swap else "ext2"):
            return "%s%d" % (device, pmax + 1)
        else:
            run_error(_("Couldn't add new partition to %s") % device)
            return ""


    def mkswap(self, partition, check):
        """Format the given swap partition. I don't know what happens if
        check is True and bad blocks are found, so including it is a bit
        pointless, but maybe I'll find out one day ...
        """
        args = [partition]
        if check:
            args.insert(0, "-c")
        return self.xlist("swap-format", *args)[0]


    def gettotalMB(self):
        if self.totalMB > 0:
            return self.totalMB
        if self.totalMB == 0:
            self.totalMB = -1
            # Start a background thread to estimate the size
            command.simple_thread(self.bgproc, "1system-size",
                    [], self._setsize)
        # but for now return 0
        return 0

    def _setsize(self, textlines):
        line = textlines.strip()
        rem = re.search(r"(\d+)\s*MB\s+total", line)
        self.totalMB = int(rem.group(1)) if rem else 0


    def set_partlist(self, plist):
        """The partition list consists of lists:
            [mount-point, device, format, uuid/label info]
        The first entry should be for root ("/"), swap partitions
        have mount-point "swap".
        The format entry is the desired formatting for the partition,
        e.g. "ext4" or "jfs". If it is empty, no formatting will be
        performed. Swap partitions are formatted when they are created,
        so they have this field empty.
        The final entry has one of the following forms:
            None: before it has been set
            /dev/sdxn: using straight device names
            LABEL=xxxxx: using partition labels
            UUID=xxxxx: using UUIDs
        plist may have only 3-entry items.
        """
        self.partition_list = []
        for p in plist:
            if len(p) == 3:
                p.append(None)
            self.partition_list.append(p)
        self.partition_list.sort()  # in case of mounts within mounts


    def set_label(self, mp, dn):
        """Set the uuid/label info for the given partition
        (see self.set_partlist).
        """
        for p in self.partition_list:
            if p[0] == mp:
                p[3] = dn


    def partlist(self):
        return self.partition_list


    def copy_system(self, logfun):
        if "i" in dbg_flags:
            return True
        return (self.xcheck("copy-system", IBASE, xlog=logfun,
                        onfail=_("Copying of system data failed"))
                and self.xcheck("fix-system1", IBASE,
                        onfail=_("Initial installed system tweaks failed"
                                " (see log)")))


    def delivify(self):
        return self.xcheck("fix-system2", IBASE,
                onfail=_("Failure while removing live-system modifications"
                        " (see log)"))


    def initramfs(self):
        return self.run_mount_devprocsys(self._initramfs)

    def _initramfs(self):
        return self.xcheck("do-mkinitcpio", IBASE,
                onfail=_("Problem building initramfs (see log)"))


    def usableparts(self):
        """Return a dict of information tuples for mountable partitions.
        Also swap partitions are included.
        Each entry has the form:
            device: (fstype, label, uuid, removable)
        When an item is not defined the value is None.
        """
        # First get the partition type-id for all hard disk partitions
        partid = {}
        for pline in self.fdiskl():
            partid[pline[0]] = pline[4]
        ups = {}
        for s in self.xlist("get-blkinfo")[1]:
            mo = re.match(r'(/dev/[^:]*):(?: LABEL="([^"]*)")?(?:'
                    ' UUID="([^"]*)")?(?: TYPE="([^"]*)")?', s)
            if mo:
                dev, label, uuid, fstype = mo.groups()
                if fstype in (None, "linux_raid_member", "LVM2_member"):
                    continue
                if dev.startswith("/dev/loop"):
                    continue
                rem = None
                if dev.startswith("/dev/sd"):
                    if partid.get(dev) == "fd":
                        # This test seems to be necessary because blkid
                        # sometimes returns an fs-type, rather than
                        # linux_raid_member", for the the first device
                        # in a formatted raid array
                        continue
                    rem = self.xlist("removable", dev)[1][0].strip() == "1"
                ups[dev] = (fstype, label, uuid, rem)
        return ups


    def mkdir(self, dir):
        return self.xcheck("do-mkdir", "-p", IBASE + dir,
                onfail =_("Couldn't create directory '%s'") % (IBASE + dir))


    def set_pw(self, pw, user="root"):
        if (pw == ''):
            # Passwordless login
            pwcrypt = '0'
        else:
            # Normal MD5 password
            salt = '$1$'
            for i in range(8):
                salt += random.choice("./0123456789abcdefghijklmnopqrstuvwxyz"
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            pwcrypt = crypt.crypt(pw, salt)

        self.mount()
        res = self.xcheck("setpw", IBASE, pwcrypt, user,
                onfail =_("Couldn't set password for user '%s'") % user)
        self.unmount()
        return res


    def mkdevicemap(self):
        return self.xlist("mkdevicemap", IBASE)[1]


    def fdiskl(self, parts=True):
        lines = self.xlist("fdisk-l")[1]
        if parts:
            # Return a list of information for each partition.
            # The information is itself in list form:
            #   [device, startcyl, endcyl, blocks(+-), id, type, boot]
            plist = []
            for line in lines:
                if line.startswith("/dev/"):
                    items = line.replace("*", " ").split(None, 5)
                    items.append("*" if "*" in line else "")
                    plist.append(items)
            return plist
        return lines


    def listNTFSpartitions(self):
        return self.xlist("get-ntfs-parts")[1]


    def getbootinfo(self):
        """Retrieves kernel file name and a list of initramfs files from
        the boot directory of the newly installed system.
        """
        self.mount()
        kernel = None
        inits = []
        for line in self.xlist("get-bootinfo", IBASE)[1]:
            if line.startswith('+++'):
                kernel = line.split()[1]
            else:
                inits.append(line)
        self.unmount()
        if not inits:
            run_error(_("No initramfs found"))
            return None
        if not kernel:
            run_error(_("GRUB problem:\n") + inits[0])
            return None
        return (kernel, inits)


    def readfile(self, dev, path):
        res = self.file_rw(dev, path)
        if res:
            text = "\n".join(res[1])
            if res[0]:
                return text + "\n"
            else:
                run_error(_("Couldn't read %s+%s:\n  %s")
                        % (dev, path, text))
        return ""


    def setup_grub(self, dev, path, text):
        if dev:
            res = (self.mount()
                    and self.run_mount_devprocsys(self._setup_grub, dev)
                    and self.xwritefile(text, "/boot/grub/menu.lst"))
        else:
            # Just replace the appropriate menu.lst
            d, p = path.split(':')
            res = self.file_rw(d, p, text)
        if self.unmount() and res:
            return True
        return False

    def _setup_grub(self, dev):
        return self.xlist("grubinstall", IBASE, dev)[0]


class DiskInfo:
    """Get info on drive and partitions.

    It uses 'fdisk -l' to get the information about the drive.
    The output of the call is parsed to extract useful information.
    Of course the instance must be discarded as soon as changes are
    made to the device.
    """
    def __init__(self, device):
        self.device = device
        info = backend.xlist("fdisk-l", device)[1]
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
        ok, l = backend.xlist("get-blkinfo", self.device, "TYPE")
        if ok and l:
            return l[0]
        else:
            return ""

    def sizeGB(self):
        l = backend.xlist("partsizes", self.device)[1]
        return float(l[0].split()[1]) / 1e9
