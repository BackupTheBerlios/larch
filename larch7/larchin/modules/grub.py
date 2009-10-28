# grub.py - set up grub bootloader
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
# 2009.10.28

doc = _("""
<h2>Set up the GRUB bootloader</h2>
<p>GRUB allows the booting of more than one operating system.
Normally it will be installed to the 'master boot record' on the
first disk drive. Here it can be installed to the mbr of the drive
on which /boot of the new installation is found - which may or may not be
the same as the root (/) partition.
</p>
<p>It may also be installed to the partition containing /boot.
Alternatively, the new Linux system can be booted from an
existing GRUB set-up by adding the entries for the new system to its
menu.lst file.
</p>
<p>A further option is to add the entries from an existing menu.lst to
those arising from the new installation, so that the operating systems
therein can still be booted, but from the newly installed bootloader.
</p>
<p>If an NTFS formatted partition is detected it will be added to the list
automatically.
</p>
<h3>WARNING</h3>
<p>If you have mixed IDE(PATA)/SCSI/SATA devices attached it is quite
possible that GRUB will get confused about their order. In other words you
might find that the association of GRUB names (hd0, hd1, etc.) to Linux
device names (/dev/sda, /dev/sdb, etc.) is incorrect. The result is
probably that you will not be able to boot your new system. In this case
you will have to manually edit menu.lst and put the correct number after
the 'hd' device entries.
</p>""")


import time, re


class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&grub!", self.select_page),
                ("grub:mbr*toggled", self.mbrtoggled),
                ("grub:old*toggled", self.oldtoggled),
                ("grub:part*toggled", self.parttoggled),
                ("grub:xmenulist*changed", self.select_old),
                ("grub:include*toggled", self.includetoggled),
                ("grub:newedit*clicked", self.editnew),
                ("grub:edit*clicked", self.editmbr),
                ("&grubsetup&", self.grubsetup),
            ]

    def __init__(self, index):
        self.page_index = index

        ui.newwidget("RadioButton", "^grub:mbr",
                text=_("Install GRUB to MBR - make it the main bootloader"))
        ui.newwidget("RadioButton", "^grub:old",
                text=_("Add new installation to existing GRUB menu"))
        ui.newwidget("RadioButton", "^grub:part",
                text=_("Install GRUB to installation partition"))

        ui.newwidget("Label", "grub:pic", image="images/grub.png")
        ui.newwidget("Frame", "grub:xmenulist-frame")
        ui.newwidget("Label", "grub:oldl",
                text=_("Choose existing menu.lst:"))
        ui.newwidget("ComboBox", "^grub:xmenulist", #width=300,
                tt=_("Select the partition with the relevant menu.lst"))

        ui.newwidget("CheckBox", "^grub:include",
                text=_("Include existing menu"),
                tt=_("The boot lines from an existing menu.lst can be"
                        " included in the new file"))

        ui.newwidget("Button", "^grub:newedit", text=_("Edit boot options"),
                tt=_("Options for booting the new installation are\n"
                        "generated automatically. You can edit them here."))

        ui.newwidget("Button", "^grub:edit", text=_("Edit menulst.conf"),
                tt=_("The automatically generated menulst.conf can be"
                        " edited.\nBut if you change some options your"
                        " new version may be lost."))

        ui.layout("page:grub", ["*VBOX*",
                "grub:mbr", "grub:old", "grub:part",
                ["*HBOX*", "grub:pic",
                    ["*VBOX*", "grub:xmenulist-frame", "*SPACE",
                        "grub:newedit", "grub:edit"]]])

        ui.layout("grub:xmenulist-frame", ["*VBOX*",
                "grub:oldl", "grub:xmenulist", "grub:include"])


    def setup(self):
        return


    def select_page(self, init):
        command.pageswitch(self.page_index, _("Configure Bootloader"))


    def init(self):
        # Set up grub's device map and a list of existing menu.lst files.
        if not self.set_devicemap():
            run_error(_("Couldn't get device map for GRUB"))

        # There is also the list of device / menu.list-path pairs
        ui.command("grub:xmenulist.set", [":".join(i)
                for i in self.xmenulist])
        self.old_index = 0
        self.oldwhere = (":".join(self.xmenulist[0]) if self.xmenulist[0]
                else None)
        ui.command("grub:xmenulist-frame.enable", False)

        # I share the extraneous menu.lst choice between the
        # options 'Add to other menu.lst' and 'Include other menu.lst'
        ui.command("grub:xmenulist-frame.enable", self.xmenulist != [])
        ui.command("grub:old.enable", self.xmenulist != [])
        ui.command("grub:mbr.set", True)

        self.ntfsboot = None
        # Seek likely candidate for Windows boot partition
        dinfo = backend.fdiskl()
        nlist = backend.listNTFSpartitions()
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


    def ok(self):
        command.runsignal("&grubsetup&")


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

        if backend.setup_grub(device, path, self.getmenulst()):
            command.runsignal("&tweaks!")
        else:
            run_error(_("GRUB setup failed - see log"))


##################################

    def set_devicemap(self):
        """Generate a (temporary) device.map file on the target and read
        its contents to a list of pairs in self.device_map.
        It also scans all partitions for menu.lst files, which are
        then stored as (device, path) pairs, in the list self.xmenulist.
        """
        if backend.mount():
            # Filter out new system '/' and '/boot'
            bar = []
            for md in backend.partlist():
                if md[0] in ('/', '/boot'):
                    bar.append(md[1])

            self.device_map = []
            self.xmenulist = []
            for line in backend.mkdevicemap():
                spl = line.split()
                if (spl[0].startswith('(')):
                    self.device_map.append(spl)
                elif (spl[0] == '+++'):
                    d = self.grubdevice(spl[2])
                    if d not in bar:
                        self.xmenulist.append((d, spl[1]))
            return backend.unmount() and (self.device_map != [])
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


    def newgrubentries(self):
        # look for separate boot partition
        self.bootpart = None
        for m, d, f, l in backend.partlist():
            if (m == '/'):
                self.rootpart = d
                self.rootname = l
            elif (m == '/boot'):
                self.bootpart = d
        # add an entry for each initramfs
        text = "# ++++ Section added by larchin (%s)\n\n" % time.ctime()
        bi = backend.getbootinfo()
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
