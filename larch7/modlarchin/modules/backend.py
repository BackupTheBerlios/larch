# backend.py
#
# (c) Copyright 2010 Michael Towers (larch42 at googlemail dot com)
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
# 2010.02.10

# Mount point for the installation root partition
IBASE = "/tmp/larchin/install"
# File containing partitioning and mount-point info
PARTLIST = "/tmp/larchin/partlist"
# File to prevent two instances of larchin from running
LOCKFILE = "/tmp/larchin/lock"


from subprocess import Popen, PIPE, STDOUT
import sys, traceback, os, re, __builtin__
__builtin__.base_dir = os.path.dirname(os.path.dirname(
        os.path.realpath(__file__)))


def start_translator():
    import gettext
    gettext.install('larchin', base_dir+'/i18n', unicode=1)


def init(io, app_quit=None):
    global quit_function
    quit_function = app_quit if app_quit else sys.exit
    __builtin__.io = io

    def debug(text):
        sys.stderr.write("DEBUG: " + text.strip() + "\n")
        sys.stderr.flush()
    __builtin__.debug = debug

    def sys_quit(rc):
        if not mounting.unmount():
            rc = 101
        os.remove(LOCKFILE)
        quit_function(rc)
    __builtin__.sys_quit = sys_quit

    def errout(message="ERROR", quit=0):
        io.out('!>' + message, True)
        if quit:
            scripts.killall()
            scripts.wait()
            sys_quit(quit)
    __builtin__.errout = errout

    # Catch all unhandled errors.
    def errortrap(type, value, tb):
        etext = "".join(traceback.format_exception(type, value, tb))
        for line in etext.splitlines():
            io.out('!+' + line, True)
        errout(_("Something went wrong, quitting (see log)"), 100)
    sys.excepthook = errortrap

    # Check no other larchin instance is running
    if os.path.isfile(LOCKFILE):
        if not io.query_yn(_(
                "Another instance of the installer seems to be running already."
                "$If you are absolutely sure no other installer instance is"
                "$running, you may continue. Otherwise you should cancel."
                "$$Shall I continue?")):
            quit_function(102)

    __builtin__.scripts = Scripts(base_dir + "/scripts/")
    __builtin__.mounting = Mounting()

    # Check nothing mounted under install mount-point
    mp = mounting.mount_point()
    mpa = mp.split('/')
    mpl = len(mpa)
    for d, m in Devices().get_mounts():
        if m.split('/')[:mpl] == mpa:
            errout(_("Installation mount-point (%s) in use") % mp, 103)


class Mounting:
    def __init__(self):
        # Keep a record of mounts (list of absolute mount-points)
        self.mounts = []

    def mount_point(self, subpath=''):
        """Returns the given path mapped into the mounted installation.
        """
        p = subpath.lstrip('/')
        return IBASE + '/' + p if p else IBASE

    def remount(self, mp, opt):
        if scripts.run("do-mount", "-o", "remount," + opt, mp):
            return True
        errout(_("Couldn't remount '%s' %s") % (mp, opt))
        return False

    def mountbind(self, dir, mp=""):
        mpb = self.mount_point(mp)
        if scripts.run("do-mount", "--bind", dir, mpb):
            self.mounts.append(mpb)
            return True
        errout(_("Couldn't bind-mount %s at %s") % (dir, mpb))
        return False

    def run_mount_devprocsys(self, script, *args):
        ok = True
        dirs = []
        for d in ("/dev", "/proc", "/sys"):
            if self.mountbind(d, d):
                dirs.append(self.mount_point(d))
            else:
                ok = False
                break
        if ok:
            ok = scripts.run(script, *args)
        return self.unmount(dirs) and ok

    def mount(self):
        partitions = Partlist().get_all()
        if partitions[0][0] != "/":
            errout(_("No root partition ('/') specified"))
            return False
        mlist = []
        for part in partitions:
            mp, dev = part[0], part[1]
            if mp.startswith("/"):
                io.out("#>" + _("Mounting %s at %s") % (dev, mp))
                mlist.append((dev, mp))
        return self.imounts(mlist)

    def imounts(self, mlist):
        self.mountlist = mlist
        for d, m in mlist:
            if not self.imount(d, m):
                return False
        return True

    def imount(self, dev, mp):
        mpreal = self.mount_point(mp)
        if scripts.run("do-imount", self.mount_point(), dev, mp):
            self.mounts.append(mpreal)
            return True
        errout(_("Couldn't mount %s at %s") % (dev, mpreal))
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
            if scripts.run("do-unmount", m):
                self.mounts.remove(m)
            else:
                errout(_("Couldn't unmount %s") % m)
                r = False
        return r

    def mkdir(self, dir):
        d = self.mount_point(dir)
        if scripts.run("do-mkdir", "-p", d):
            return True
        errout(_("Couldn't create directory '%s'") % d)
        return False


class Scripts:
    def __init__(self, scriptdir):
        self.scriptdir = scriptdir
        self.processes = []

    def script(self, *args):
        p = self.start_script(*args)
        op = p.communicate()[0]
        self.processes.remove(p)
        return p.returncode, op

    def start_script(self, scriptname, *args):
        p = Popen((self.scriptdir + scriptname,) + args,
                stdout=PIPE, stderr=STDOUT)
        self.processes.append(p)
        return p

    def end_script(self, p):
        p.wait()
        self.processes.remove(p)
        return p.returncode==0

    def run(self, *args):
        p = self.start_script(*args)
        while True:
            line = p.stdout.readline()
            if not line:
                break
            io.out("##" + line.rstrip())
        # The process has ended.
        return self.end_script(p)

    def killall(self):
        for p in self.processes:
            Popen(["pkill", "-g", str(p.pid)], stdout=PIPE).communicate()

    def wait(self):
        for p in list(self.processes):
            p.wait()


class Partlist:
    """This handles the current list of installation partitions.
    Device names, Formatting, Mount-points are managed, these being stored
    in the file system to provide a measure of persistence.
    The partition list consists of lists:
        [mount-point, device, format, uuid/label info]
    The first entry should be for root ("/"), swap partitions
    have mount-point "swap".
    The format entry is the desired formatting for the partition,
    e.g. "ext4" or "jfs". If it is empty, no formatting will be
    performed. Swap partitions should be formatted when they are created,
    so they have this field empty.
    The final entry has one of the following forms:
        (empty): before it has been set
        -: using straight device names
        LABEL=xxxxx: using partition labels
        UUID=xxxxx: using UUIDs
    """
    def __init__(self, plist=[]):
        if (not plist) and os.path.isfile(PARTLIST):
            fh = open(PARTLIST)
            plist = fh.read().splitlines()
            fh.close()
        self.partition_list = []
        fail = False
        for line in plist:
            p = [i.strip() for i in line.split(':')]
            while len(p) < 4:
                p.append('')
            try:
                assert p[1].startswith('/dev/')
                assert p[2] in ('', 'ext2', 'ext3', 'ext4', 'reiserfs',
                        'jfs', 'xfs')
                assert p[3].split('=')[0] in ('', '-', 'LABEL', 'UUID')
                self.partition_list.append(p)
            except:
                errout(_("Bad partition descriptor: %s") % line)
                fail = True

        if fail:
            self.partition_list = []
        self.save()

    def save(self):
        try:
            pd = os.path.dirname(PARTLIST)
            if not os.path.isdir(pd):
                os.makedirs(pd)
            fh = None
            fh = open(PARTLIST, 'w')
            for line in self.partition_list:
                fh.write(':'.join(line) + '\n')
            return True
        except:
            errout(_("Couldn't save partition data to %s") % PARTLIST, quit=99)
        finally:
            if fh:
                fh.close()

    def get_all(self):
        return self.partition_list

    def set_label(self, mp, dn):
        """Set the uuid/label info for the given partition
        """
        for p in self.partition_list:
            if p[0] == mp:
                p[3] = dn
        self.save()


class Devices:
    def get_mounts(self):
        """Return a list of mounted (partition, mount-point) pairs.
        """
        return [m.split() for m in scripts.script("get-mounts")[1]]

    def get_mountable(self):
        """Get a dict of all 'mountable' partitions.
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
        for s in scripts.script("get-blkinfo")[1]:
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
                    rem = scripts.script("removable", dev)[1][0].strip() == "1"
                ups[dev] = (fstype, label, uuid, rem)
        return ups

    def fdiskl(self, parts=True):
        lines = scripts.script("fdisk-l")[1]
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
