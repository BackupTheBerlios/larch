#!/usr/bin/env python
#
# grub.py - set up grub bootloader
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
# 2010.03.03

"""
mbr:
 possibility of chain-loading other bootloaders

partition:
 no sense in including other stuff, but you will want to be able
to chain-load this partition from somewhere else, which is not necessarily
straightforward.

 The problem with adjusting the configuration of other bootloaders is that
there is a variety of approaches to handling these. Some linux distributions
have tools to update these automatically from possibly non-standard source
files, and the standard configuration files should not be edited.
At least initially I think it would be best to let the user make such
changes manually. She can use the generated menu.lst (which in this case
should contain only entries for the new installation) as a basis.

 I think a sensible approach might be to install a small 'live' rescue
system in one partition, this also accommodating the main (MBR) bootloader.
From here any other OSes can be chain-loaded or - if they also use GRUB -
their configfile can be loaded. In any case I think this is possibly an
improvement over the old idea of putting /boot on its own partition.

 In order to aid manual editing of entries, it might be an idea to provide
an editor interface - say a function call with the test to be edited, the
result being returned for saving, with special returns for cancellation,
etc. As in the old code, there can be additional (functional?) arguments
for reversion, etc.
"""

import time, re
import backend

class Grub:

    def init(self, partlist0=[]):
        """Set up grub's device map and a list of existing menu.lst files.
        Also set self.rootpart and self.rootname from the partition list,
        and self.bootpart if /boot is on a separate partition.
        """
        debug("plist0 " + repr(partlist0))
        self.partlist = backend.Partlist(partlist0).get_all()
        debug("plist " + repr(self.partlist))
        if not self.partlist:
            return False
        if not self.scan_devices():
            errout(_("Couldn't get device map for GRUB"))
            return False
        # look for separate boot partition
        self.bootpart = None
        for m, d, f, l in self.partlist:
            if (m == '/'):
                self.rootpart = d
                self.rootname = l
            elif (m == '/boot'):
                self.bootpart = d
        return True


    def get_existing(self):
        """Return a list of partitions containing grub configuration files:
            [(device, path)]
        """
        return self.xmenulist


    def get_menu_lst_base(self):
        return backend.readdata("menu_lst_base")


    def install(self, mbr=False, extra=True):
        """Install grub to the MBR or to the installation's boot partition.
        """
        if self.bootpart:
            bootdevice = self.bootpart
            path = '/grub/menu.lst'
        else:
            bootdevice = self.rootpart
            path = '/boot/grub/menu.lst'
        if mbr:
            device = bootdevice.rstrip("0123456789")
        else:
            device = bootdevice

        menulst = self.get_menu_lst_base() + self.newgrubentries(extra and mbr)
        if self.install_grub(menulst, device):
            return '%s:%s' % (bootdevice, path)
        return None


    def install_grub(self, menu_lst, device):
        """Set up GRUB on the given device, writing menu_lst
        to /boot/grub/menu.lst.
        """
        res = (mounting.mount()
                and mounting.run_mount_devprocsys("grubinstall",
                        mounting.mount_point(), device)
                and backend.writefile(menu_lst,
                        mounting.mount_point("/boot/grub/menu.lst")))
        if (mounting.unmount() and res):
            return True
        errout(_("GRUB setup failed - see log"))
        return False


    def scan_devices(self):
        """Generate a device.map file on the target and read
        its contents to a list of pairs in self.device_map.
        It also scans all partitions for menu.lst and grub.cfg files,
        which are then stored as (device, path) pairs, in the list
        self.xmenulist.
        """
        if mounting.mount():
            # Filter out new system '/' and '/boot'
            bar = []
            for md in self.partlist:
                if md[0] in ('/', '/boot'):
                    bar.append(md[1])

            self.device_map = []
            self.xmenulist = []
            for line in scripts.script("mkdevicemap").splitlines():
                spl = line.split()
                if (spl[0].startswith('(')):
                    self.device_map.append(spl)
                elif (spl[0] == '+++'):
                    d = self.grubdevice(spl[2])
                    if d not in bar:
                        self.xmenulist.append((d, spl[1]))
            return mounting.unmount() and (self.device_map != [])
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


    def newgrubentries(self, extra=False):
        """Generate the grub menu.lst entries for the new installation.
        If extra is True also add section for other, discovered partitions.
        """
        # add an entry for each initramfs
        text = "# ++++ Section added by larchin (%s)\n\n" % time.ctime()
        bi = self.getbootinfo()
        if not bi: return ""
        kernel, inits = bi
        if self.bootpart:
            rp = self.grubdevice(self.bootpart)
            bp = ""
        else:
            rp = self.grubdevice(self.rootpart)
            bp = "/boot"
        for init in inits:
            titlepart = self.rootpart
            if self.rootname.startswith("UUID="):
                titlepart += ' (UUID)'
                r = "/dev/disk/by-uuid/%s" % self.rootname.split("=", 1)[1]
            elif self.rootname.startswith("LABEL="):
                titlepart = self.rootname
                r = "/dev/disk/by-label/%s" % self.rootname.split("=", 1)[1]
            else:
                r = self.rootpart
            text += "title  Arch Linux %s (initrd=/boot/%s)\n" % (
                    titlepart, init)
            text += "root   %s\n" % rp
            text += "kernel %s/%s root=%s ro\n" % (bp, kernel, r)
            text += "initrd %s/%s\n\n" % (bp, init)

        if extra:
            # GRUB partitions
            for dev, path in self.get_existing():
                text += "\n# ....\n"
                if path.endswith('menu.lst'):
                    text += "title Other GRUB menu (%s)\n" % dev
                    text += "root %s\n" % self.grubdevice(dev)
                    text += "configfile %s\n" % path
                else:
                    text += "title GRUB2 Bootloader (%s)\n" % dev
                    text += "root %s\n" % self.grubdevice(dev)
                    text += "makeactive\n"
                    text += "chainloader +1\n\n"

            # Windows partitions
            ntfsboot = self.get_ntfsboot()
            if ntfsboot:
                text += "\n# ....\n"
                text += "title Windows\n"
                text += "rootnoverify %s\n" % self.grubdevice(ntfsboot)
                text += "makeactive\n"
                text += "chainloader +1\n\n"

        text += "# ---- End of section added by larchin\n"
        self.newentries = text
        return text


    def getbootinfo(self):
        """Retrieve kernel file name and a list of initramfs files from
        the boot directory of the newly installed system.
        """
        mounting.mount()
        kernel = None
        inits = []
        for line in scripts.script("get-bootinfo",
                mounting.mount_point()).splitlines():
            if line.startswith('+++'):
                kernel = line.split()[1]
            else:
                inits.append(line)
        mounting.unmount()
        if not inits:
            errout(_("No initramfs found"))
            return None
        if not kernel:
            errout(_("Kernel not found:\n") + inits[0])
            return None
        return (kernel, inits)


    def get_ntfsboot(self):
        """Seek likely candidate for Windows boot partition.
        """
        ntfsboot = None
        devices = backend.Devices()
        dinfo = devices.fdiskl()
        np = scripts.script("get-ntfs-parts")
        if np:
            nlist = np.splitlines()
            for p in dinfo:
                # First look for (first) partition marked with boot flag
                if p[6] and p[0] in nlist:
                    ntfsboot = p[0]
                    break
            if (ntfsboot == None) and nlist:
                # Else just guess first NTFS partition
                ntfsboot = nlist[0]
        return ntfsboot


if __name__ == "__main__":
    import console
    backend.start_translator()

    from optparse import OptionParser, OptionGroup
    parser = OptionParser(usage=_("usage: %prog [options]"))
    parser.add_option("-m", "--mbr", action="store_true", dest="mbr",
            default=False,
            help=_("Install GRUB to Master Boot Record of installation device"))
    parser.add_option("-x", "--exclude", action="store_false", dest="include",
            default=True, help=_("Exclude entries for other bootloaders"))
    parser.add_option("-n", "--noinstall", action="store_true", dest="noinstall",
            default=False, help=_("Don't install GRUB, just print boot entries"))
    parser.add_option("-b", "--listboot", action="store_true", dest="list",
            default=False, help=_("List other, discovered bootloaders"))
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
            default=False, help=_("Suppress output messages, except errors"))
    group = OptionGroup(parser, _("Passing installation partitions"),
            _("   mount-point:device:format:uuid/label ..."
            " More than one such descriptor can be passed, using ',' as"
            " separator.   The first entry should be for root"
            " (mount-point is '/'), swap partitions have mount-point 'swap'."
            "   format should be 'ext4' or 'jfs', for example. If it is"
            " empty, no formatting will be performed. Also swap"
            " partitions should have this field empty.   The final entry"
            " may be empty (implying the system default will be used),"
            " otherwise:   "
            "   -: using straight device names (/dev/sdXN),"
            "   LABEL=xxxxx: using partition labels,"
            "   UUID=xxxxx: using UUIDs"))
    group.add_option("-l", "--partitions", action="store", type="string",
            default="", dest="parts", help=_("Pass partition list"),
            metavar="PARTLIST")
    parser.add_option_group(group)
    (options, args) = parser.parse_args()

    backend.init(console.Console(options.quiet))

    grub = Grub()
    if not grub.init(options.parts):
        sys_quit(1)

    if options.list:
        io.out(_("Partitions containing bootloader configuration files:"))
        for dp in grub.get_existing():
            io.out("    %s: %s" % dp, True)

    if options.noinstall:
        io.out(_("Not installing GRUB!"))
        lines = grub.newgrubentries(options.include and options.mbr)
        io.out(_("Boot entries:"))
        for line in lines.splitlines():
            io.out("  >  %s" % line, True)
    else:
        io.out(_("Installing GRUB!"))
        r = grub.install(options.mbr, options.include)
        if r:
            io.out(r)
        else:
            errout(_("GRUB installation failed"))
            sys_quit(2)

    sys_quit(0)
