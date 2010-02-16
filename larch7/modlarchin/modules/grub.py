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
# 2010.02.14


import time, re


class Grub:

    def init(self):
        # Set up grub's device map and a list of existing menu.lst files.
        if not self.set_devicemap():
            errout(_("Couldn't get device map for GRUB"))
            return False

        self.ntfsboot = None
        # Seek likely candidate for Windows boot partition
        devices = Devices()
        dinfo = devices.fdiskl()
        nlist = scripts.script("get-ntfs-parts").splitlines()
        for p in dinfo:
            # First look for (first) partition marked with boot flag
            if p[6] and p[0] in nlist:
                self.ntfsboot = p[0]
                break
        if (not self.ntfsboot) and nlist:
            # Else just guess first NTFS partition
            self.ntfsboot = nlist[0]

        self.newgrubentries()
        self.includetoggled(False)

# Do we want to pass an initial partlist to the constructor?
        self.partlist = backend.Partlist(???)


    def mbrtoggled(self, on):
        if on:
            self.where = "mbr"


    def oldtoggled(self, on):
        if on:
            self.where = "old"
        ui.command("grub:include.enable", not on)
        self.newmenulst()


    def parttoggled(self, on):
        if on:
            self.where = "part"


    def includetoggled(self, on):
        self.include = on
        self.newmenulst()


    def select_old(self, index=-1):
        if index < 0:
            return
        self.old_index = index
        self.oldwhere = ":".join(self.xmenulist[index])
        self.newmenulst()


    def editnew(self):
        ui.edit(_("Bootloader entries for new installation"),
            self.setnewentries, self.newentries, self.newgrubentries)


    def setnewentries(self, text):
        self.newentries = text


    def editmbr(self):
        ui.edit(_("New menu.lst"),
            self.newmenulst, self.getmenulst(), self.revert)


    def revert(self):
        self.newmenulst()
        return self.getmenulst()


    def grubsetup(self):
        if (self.where == 'old'):
            # Add this installation to an already existing menu.lst
            device = None
            path = self.oldwhere
        else:
            # Install grub to partition or mbr
            if self.bootpart:
                device = self.bootpart
            else:
                device = self.rootpart
            if self.where == 'mbr':
                device = device.rstrip("0123456789")
            path = None

        text = self.getmenulst()
        if not text:
            errout(_("Couldn't construct GRUB menu - see log"))
            return False

        if device:
            res = (mounting.mount()
                    and scripts.run_mount_devprocsys("grubinstall",
                            mounting.mount_point(), device)
                    and backend.writefile(text,
                            mounting.mount_point("/boot/grub/menu.lst")))
        else:
            # Just replace the appropriate menu.lst
            d, p = path.split(':')
            res = backend.file_rw(d, p, text)
        if mounting.unmount() and res:
            return True
        errout(_("GRUB setup failed - see log"))
        return False


##################################

#done
    def set_devicemap(self):
        """Generate a (temporary) device.map file on the target and read
        its contents to a list of pairs in self.device_map.
        It also scans all partitions for menu.lst files, which are
        then stored as (device, path) pairs, in the list self.xmenulist.
        """
        if mounting.mount():
            # Filter out new system '/' and '/boot'
            bar = []
            for md in backend.partlist():
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


#(done)
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


    def newmenulst(self, text=None):
        self.menulst = text


    def getmenulst(self):
        if self.menulst == None:
            if self.where != "old":
                # Get template
                text = command.readfile("menu_lst_base")

                # Add entries for new installation
                text += self.newentries

                # add old entries
                if self.include:
                    dev, path = self.oldwhere.split(':')
                    ml = backend.readfile(dev, path)
                    # Take everything from the first 'title'
                    mlp = re.compile(".*?^(title.*)", re.M | re.S)
                    m = mlp.search(ml)
                    if m:
                        text += "\n" + m.group(1)

            else:
                # Get existing menu.lst
                dev, path = self.oldwhere.split(':')
                text = backend.readfile(dev, path)

                # Add entries for new installation
                text += "\n" + self.newentries

            self.menulst = text

        return self.menulst


#done
    def newgrubentries(self):
        # look for separate boot partition
        self.bootpart = None
        for m, d, f, l in self.partlist().get_all():
            if (m == '/'):
                self.rootpart = d
                self.rootname = l
            elif (m == '/boot'):
                self.bootpart = d
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
            text += "title  Arch Linux %s (initrd=/boot/%s)\n" % (
                    self.rootpart, init)
            text += "root   %s\n" % rp

            if self.rootname.startswith("UUID="):
                r = "/dev/disk/by-uuid/%s" % self.rootname.split("=", 1)[1]
            elif self.rootname.startswith("LABEL="):
                r = "/dev/disk/by-label/%s" % self.rootname.split("=", 1)[1]
            else:
                r = self.rootpart
            text += "kernel %s/%s root=%s ro\n" % (bp, kernel, r)
            text += "initrd %s/%s\n\n" % (bp, init)

        if self.ntfsboot:
            text += "# ....\n"
            text += "title Windows\n"
            text += "rootnoverify %s\n" % self.grubdevice(self.ntfsboot)
            text += "makeactive\n"
            text += "chainloader +1\n\n"

        text += "# ---- End of section added by larchin\n"
        self.newentries = text
        return text


#done
    def getbootinfo(self):
        """Retrieves kernel file name and a list of initramfs files from
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
            errout(_("GRUB problem:\n") + inits[0])
            return None
        return (kernel, inits)
