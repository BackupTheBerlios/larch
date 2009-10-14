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
# 2009.10.12

from subprocess import Popen, PIPE, STDOUT
import os, threading
import re


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

        #self.interrupt = 0
        #self.error = None
        #self.outputmethod = None


#???
        # Keep a record of mounts
        self.mounts = []


#TODO: Maybe this should be done outside of __init__
#        if (self.xcall("init") != ""):
#            fatal_error(_("Couldn't initialize installation system"))


# I am not using this at the moment, I just thought it might be useful.
    def read_output_cb(self, textline):
        """By setting self.outputmethod to a (gui thread) method, the
        output of an xcall command can be processed line-by-line in the gui.
        """
        self.outputmethod(textline)
        return False        # So this method is not repeatedly called


    #************ Methods for calling bash scripts

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
        xcmd = ("%s/syscalls/%s" % (basePath, cmd))
        return Popen(xcmd, shell=True, stdout=PIPE, stderr=STDOUT, bufsize=1)


    def _xcall_net(self, cmd, opt=""):
        """Call a function on another machine.
        Public key authentication must be already set up so that no passsword
        is required.
        """
        xcmd = ("ssh %s root@%s /opt/larchin/syscalls/%s" %
                (opt, self.host, cmd))
        return Popen(xcmd, shell=True, stdout=PIPE, stderr=STDOUT, bufsize=1)


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


    def xlist(self, cmd, opt=""):
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


    def killprocess(self):
        self.process_lock.acquire()
        if self.process:
            self.process.kill()
            self.interrupt = 1
        self.process_lock.release()


#??? - do I need these? (in modified form!)
    def mount(self, src, dst, opts=""):
        if supershell("mount %s %s %s" % (opts, src, dst)).ok:
            self.mounts.append(dst)
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
        for m in mounts:
            if supershell("umount %s" % m).ok:
                self.mounts.remove(m)
            else:
                r = False
        return r

########################################################################
# Interface functions

    def rmparts(self, dev, partno):
        """Remove all partitions on the given device starting from the
        given partition number.
        """
        parts = DiskInfo(dev).parts
        parts.reverse()
        for p in parts:
            pn = int(p[0][8:])
            if (pn >= partno) and not self.xlist("rmpart %s %d" % (dev, pn))[0]:
                run_error(_("Couldn't remove partition %s") % p[0])
                return False
        return True


    def newpart(self, device, primary, ncyls, startcyl=-1, swap=False):
        """Create a partition on the given device.
        If startcyl is not given, assume the partition is to be created
        immediately after the last occupied cylinder.
        Only Linux and Linux Swap partition types are supported.
        Return the partition number of the created partition.
        """
        di = DiskInfo(device)
#TODO
# Do I want to handle resizing of an extended partition to accommodate
# new partitions, or do I just allocate all remaining space to it when
# the first logical partition is added? If I use the latter approach
# it would mean any elaborate editing would have to be delegated to
# gparted or cfdisk.

        # Use: parted -s self.device unit cyl mkpart primary ext2 0 20
        # or whatever to create the partition



    def mkswap(self, partition, check):
        """Format the given swap partition. I don't know what happens if
        check is True and bad blocks are found, so including it is a bit
        pointless, but maybe I'll find out one day ...
        """
        self.xlist("swap-format " + ("-c " if check else "") + partition)


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

    def get_freecyls(self):
        """Assume the free space is at the end of the drive!
        Return the number of free cylinders at the end of the device.
        """
        lastcyl = 0
        for p in self.parts:
            if p[2] > lastcyl:
                lastcyl = p[2]
        return self.drvcyls - lastcyl - 1   # cylinder numbers start at 0






