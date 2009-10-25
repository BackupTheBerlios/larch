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
# 2009.10.25

doc = _("""
<h2>Set up the GRUB bootloader</h2>
<p>GRUB allows the booting of more than one operating system.
Normally it will be installed to the 'master boot record' on the
first disk drive, but the new Linux system can also be booted from an
existing GRUB set-up.
</p>""")


import time


class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&grub!", self.select_page),
                ("grub:mbr*toggled", self.mbrtoggled),
                ("grub:old*toggled", self.oldtoggled),
                ("grub:part*toggled", self.parttoggled),
                ("grub:device-list*select", self.select_mbr),
                ("grub:xmenulist*changed", self.select_old),
                ("grub:include*toggled", self.includetoggled),
                ("grub:edit*clicked", self.editmbr),
            ]

    def __init__(self, index):
        self.page_index = index

        ui.newwidget("RadioButton", "^grub:mbr",
                text=_("Install GRUB to MBR - make it the main bootloader"))
        ui.newwidget("RadioButton", "^grub:old",
                text=_("Add new installation to existing GRUB menu"))
        ui.newwidget("RadioButton", "^grub:part",
                text=_("Install GRUB to installation partition"))

        ui.newwidget("Frame", "grub:mbr-frame",
                text=_("Select device for MBR"))
        ui.newwidget("List", "^grub:device-list", selectionmode="Single",
                tt=_("Select the drive to whose MBR grub should be installed"))
        ui.command("grub:device-list.setHeaders", [_("Device"),
                _("Size"), _("Model")])

        ui.newwidget("Frame", "grub:xmenulist-frame")
        ui.newwidget("Label", "grub:oldl",
                text=_("Choose existing menu.lst:"))
        ui.newwidget("ComboBox", "^grub:xmenulist", width=300,
                tt=_("Select the partition with the relevant menu.lst"))

        ui.newwidget("CheckBox", "^grub:include",
                text=_("Include existing menu"),
                tt=_("The boot lines from an existing menu.lst can be"
                        " included in the new file"))

        ui.newwidget("Button", "^grub:edit", text=_("Edit menulst.conf"),
                tt=_("The automatically generated menulst.conf can be"
                        " edited.\nBut if you change some options your"
                        " new version may be lost."))

        ui.layout("page:grub", ["*VBOX*",
                "grub:mbr", "grub:old", "grub:part",
                ["*HBOX*", "grub:mbr-frame",
                    ["*VBOX*", "grub:xmenulist-frame", "grub:edit"]]])

        ui.layout("grub:mbr-frame", ["*VBOX*",
                "grub:device-list"])

        ui.layout("grub:xmenulist-frame", ["*VBOX*",
                "grub:oldl", "grub:xmenulist", "*SPACE",
                "grub:include"])


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
        ui.command("grub:xmenulist-frame.enable", False)

        self.mbrdevices = backend.get_devices()
        self.mbr_index = 0
        ui.command("grub:device-list.set", self.mbrdevices, self.mbr_index)
        ui.command("grub:device-list.compact")

# I suppose I could share the extraneous menu.lst choice between the
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


    def mbrtoggled(self, on):
        if on:
            self.where = "mbr"
        ui.command("grub:mbr-frame.enable", on)

    def oldtoggled(self, on):
        if on:
            self.where = "old"
        self.menulst = None
        ui.command("grub:include.enable", not on)

    def parttoggled(self, on):
        if on:
            self.where = "part"

    def includetoggled(self, on):
        self.include = on


    def select_mbr(self, index=-1):
        if index < 0:
            return
        self.mbr_index = index
        self.mbrdevice = self.mbrdevices[index][0]

    def select_old(self, index=-1):
        if index < 0:
            return
        self.old_index = index
        self.oldwhere = ":".join(self.xmenulist[index])
        self.oldml = self.reml_cb()


    def editmbr(self):
        return


#TODO
    def ok(self):
        if (self.where == 'mbr'):
            device = self.mbrdevice
            path = None
            text = self.menulst
        elif (self.where == 'old'):
            device = None
            path = self.oldwhere
            text = self.ml
        else:
            if self.bootpart:
                device = self.bootpart
            else:
                device = self.rootpart
            path = None
            self.menulstwhere = None
            text = self.revert_cb()

# Remove when ready
        return

        if backend.setup_grub(device, path, text):
            command.runsignal("&tweaks!")

##################################
#DONE:
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

#DONE:
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




##################################

#???
    # Stuff for 'include existing menu'
    def setimport_cb(self, devpath):
        self.menulstwhere = devpath
        self.menulst = self.revert_cb()
#???
    def editmbr_cb(self):
        newtext = popupEditor(_("Edit menu.lst"), self.menulst, self.revert_cb)
        if newtext:
            self.menulst = newtext

#???
    def revert_cb(self):
        # Get template
        text = command.readfile("menu_lst_base")

        # Add entries for new installation
        text += self.newgrubentries()

        # add old entries
        if self.menulstwhere:
            dev, path = self.menulstwhere.split(':')
            ml = backend.readfile(dev, path)
            # Take everything from the first 'title'
            mlp = re.compile(".*?^(title.*)", re.M | re.S)
            m = mlp.search(ml)
            if m:
                text += "\n" + m.group(1)

        return text
#???
    # Stuff for 'use existing menu'
    def editml_cb(self):
        newtext = popupEditor(_("Edit existing menu.lst"), self.ml,
                self.reml_cb)
        if newtext:
            self.ml = newtext

#DONE
    def reml_cb(self):
        if self.oldwhere:
            # Get existing menu.lst
            dev, path = self.oldwhere.split(':')
            text = backend.readfile(dev, path)

            # Add entries for new installation
            text += "\n" + self.newgrubentries()
        else:
            text = ""
        return text

#DONE
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
            text += "title Windows\n"
            text += "rootnoverify %s\n" % self.grubdevice(self.ntfsboot)
            text += "makeactive\n"
            text += "chainloader +1\n\n"

        return (text + "# ---- End of section added by larchin\n")

#OK?
    def getmenu(self, filestring):
        """Try to extract grub entries from the given menu.lst file contents
        (in the form of a string). Return as a list.
        """
        titles = []
        lines = filestring.splitlines(True)
        reading = False
        for l in lines:
            ls = l.strip()
            if reading:
                if (not ls) or (ls == '#'):
                    titles.append(thisone)
                    reading = False
                else:
                    thisone += l
            elif ls.startswith('title'):
                reading = True
                thisone = l
        if reading:
            titles.append(thisone + '\n')
        return titles



