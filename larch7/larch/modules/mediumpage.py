#!/usr/bin/env python
#
# mediumpage.py
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
# 2009.08.21

import os

from medium import Medium

class MediumPage:
    """This class manages the page dealing with copying the generated larch
    system to a bootable medium.
    """

    def connect(self):
        return [
                (":bootlines*clicked", self.edit_bootlines),
                (":grubtemplate*clicked", self.edit_grubtemplate),
                (":syslinuxtemplate*clicked", self.edit_syslinuxtemplate),

                (":mediumtype*changed", self.partition_toggled),



                (":$nodevice*toggled", self.search_toggled),
                (":$uuid*toggled", self.uuid_toggled),
                (":$label*toggled", self.label_toggled),
                (":$device*toggled", self.device_toggled),
                (":$grub*toggled", self.grub_toggled),
                (":$syslinux*toggled", self.syslinux_toggled),
                (":$none*toggled", self.none_toggled),
                (":selectpart*clicked", self.selectpart),
                (":changelabel*clicked", self.changelabel),
                ("$parts:list*changed$", self.part_selected),
                (":make*clicked", self.makedevice),
                (":bootcd*clicked", self.makebootiso),
            ]


    def __init__(self):
        self.mediumbuilder = Medium()


    def setup(self):
        """Set up the build page widget.
        """
        self.profile = config.get("profile")

        part = 1 if config.get("medium_iso") == "" else 0
        command.ui(":mediumtype.set", part)
        self.partition_toggled(part)

        btldr = config.get("medium_btldr")

        command.ui(":$%s.set" % btldr, True)

        search = config.get("medium_search")
        command.ui(":$%s.set" % search, True)
        command.ui(":larchboot.set", search == "nodevice")

        command.ui(":labelname.set", config.get("medium_label"))
        command.ui(":larchpart.set")


    def search_toggled(self, on):
        command.ui(":larchboot.set", on)
        _medium_search("nodevice", on)

    def uuid_toggled(self, on):
        _medium_search("uuid", on)

    def label_toggled(self, on):
        _medium_search("label", on)

    def device_toggled(self, on):
        _medium_search("device", on)


    def grub_toggled(self, on):
        _medium_btldr("grub", on)

    def syslinux_toggled(self, on):
        _medium_btldr("syslinux", on)

    def none_toggled(self, on):
        _medium_btldr("none", on)


    def partition_toggled(self, page):
        on = (page == 1)
        config.set("medium_iso", "" if on else "yes")


        command.ui(":detection.enable", on)
        command.ui(":bootcd.enable", on)


    def selectpart(self):
        # Present a list of available partitions (maybe only unmounted ones?)
        # First get a list of mounted devices
        mounteds = []
        fh = open("/etc/mtab")
        for l in fh:
            dev = l.split()[0]
            if dev.startswith("/dev/sd"):
                mounteds.append(dev)
        fh.close()
        # Get a list of partitions
        self.partlist = [(_("None"), "")]
        for line in supershell("sfdisk -uM -l").result:
            if line.startswith("/dev/sd"):
                fields = line.replace("*", "").replace(" - ", " ? ")
                fields = fields.replace("+", "").replace("-", "").split()
                #debug("F5 '%s'" % fields[5])
                if fields[5] in ["0", "5", "82"]:
                    #debug("No")
                    continue        # ignore uninteresting partitions
                if fields[0] in mounteds:
                    continue        # ignore mounted patitions
                # Keep a tuple (partition, size in MiB)
                self.partlist.append((fields[0], fields[3]))

        command.ui("parts:list.set", ["%-12s %12s %s" % (p, s, "MiB" if s else "")
                for p, s in self.partlist])
        command.ui("parts:choice.set")
        if command.uiask("parts:parts.showmodal"):
            t = command.uiask("parts:choice.get").encode("utf8")
            command.ui(":larchpart.set", t)


    def part_selected(self, i):
        if i <= 0:
            command.ui("parts:choice.set")
        else:
            command.ui("parts:choice.set", self.partlist[i][0])


    def edit_bootlines(self):
        # The profile version is at the top level in the profile because
        # it is used by both grub and syslinux/isolinux, and is actually
        # just an extension to the existing template file.
        command.edit("bootlines",
                base_dir + "/cd-root/bootlines",
                label=_("Editing larch boot entries"))


    def edit_grubtemplate(self):
        # This should be at the correct relative location to avoid confusion.
        mld = os.path.join(self.profile, "cd-root/grub/grub")
        if not os.path.isdir(mld):
            os.makedirs(mld)
        f0 = os.path.join(self.profile, "cd-root/grub0/grub/menu.lst")
        if not os.path.isfile(f0):
            f0 = os.path.join(base_dir, "cd-root/grub0/grub/menu.lst")
        command.edit(mld + "/menu.lst", f0, label=_("Editing grub template"))


    def edit_syslinuxtemplate(self):
        # This should be at the correct relative location to avoid confusion
        mld = os.path.join(self.profile, "cd-root/isolinux")
        if not os.path.isdir(mld):
            os.makedirs(mld)
        f0 = os.path.join(self.profile, "cd-root/isolinux0/isolinux.cfg")
        if not os.path.isfile(f0):
            f0 = os.path.join(base_dir, "cd-root/isolinux0/isolinux.cfg")
        command.edit(mld + "/menu.lst", f0, label=_("Editing syslinux/isolinux template"))


    def changelabel(self):
        ok, text = command.uiask("textLineDialog",
                _("Enter new label for the boot medium:"),
                None, config.get("medium_label"))
        if ok:
            text = text.strip().replace(" ", "_")
            config.set("medium_label", text)
            command.ui(":labelname.set", text)


    def makedevice(self):
        iso = config.get("medium_iso") != ""

        btype = config.get("medium_btldr")  # "grub" / "syslinux" / "none"
        if btype == "grub":
            btype = "boot"
        elif btype == "none":
            btype = ""
        elif iso:
            btype = "isolinux"

        if iso:
            device = ""
        else:
            device = command.uiask(":larchpart.get")
            if not device:
                config_error(_("No partition selected for larch"))
                return False

        label = config.get("medium_label")

        partsel = config.get("medium_search")
        # "nodevice" / "uuid" / "label" / "device"
        if partsel == "nodevice":
            partsel = ""
        elif partsel == "device":
            partsel = "partition"

        format = not command.uiask(":noformat.active")

        self.mediumbuilder.make(btype, device, label, partsel, format,
                command.uiask(":larchboot.active"))
        # btype is "boot" (grub), "syslinux", "isolinux" or "" (no bootloader)
        # For cd/dvd (iso), device is ""
        # partsel = "uuid", "label", "partition", or ""


    def makebootiso(self):
        device = command.uiask(":larchpart.get")
        if not device:
            config_error(_("The partition containing the larch live system"
                    "\nmust be specifed."))
        self.mediumbuilder.mkbootiso(device)


def _medium_search(stype, on):
    if on:
        config.set("medium_search", stype)

def _medium_btldr(btype, on):
    if on:
        config.set("medium_btldr", btype)
