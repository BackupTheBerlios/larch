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
# 2009.12.07

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
                (":search*toggled", self.search_toggled),
                (":uuid*toggled", self.uuid_toggled),
                (":label*toggled", self.label_toggled),
                (":device*toggled", self.device_toggled),
                (":grub*toggled", self.grub_toggled),
                (":syslinux*toggled", self.syslinux_toggled),
                (":none*toggled", self.none_toggled),
                ("&-:selectpart*clicked", self.selectpart),
                ("&-:changelabel*clicked", self.changelabel),
                ("&-:make*clicked", self.makedevice),
                ("&-:bootcd*clicked", self.makebootiso),
                (":cdroot*clicked", self.cdroot),
                (":sessionsave*toggled", self.sessionsaving),
                ("$*new_label*$", self.new_label),
                ("&makelive&", self.makelive),
                ("&bootiso&", self.bootiso),
            ]


    def __init__(self):
        ui.widget("Notebook", "^:mediumtype", tabs=[
                    (":medium_iso", "iso (CD/DVD)"),
                    (":medium_partition", _("Partition (disk / USB-stick)")),
                ],
                tt=_("You can choose installation to iso (for CD/DVD) or a partition (e.g. USB-stick)"))
        ui.widget("Label", ":lmiso",
                text=_("There are no options specific to iso media."))

        ui.widget("Label", ":lm2", text=_("Partition:"))
        ui.widget("LineEdit", ":larchpart", ro=True,
                tt=_("The partition to which the larch system is to be installed"))
        ui.widget("Button", "^&-:selectpart", text=_("Choose"),
                tt=_("Select the partition to receive the larch system"))
        ui.widget("CheckBox", ":noformat", text=_("Don't format"),
                tt=_("Copy the data to the partition without formatting first (not the normal procedure)"))

        ui.widget("Frame", ":detection", text=_("Medium Detection"),
                tt=_("Choose how the boot scripts determine where to look for the larch system"))
        ui.widget("RadioButton", "^:uuid", text="UUID",
                tt=_("Use the partition's UUID to find it"))
        ui.widget("RadioButton", "^:label", text="LABEL",
                tt=_("Use the partition's label to find it"))
        ui.widget("RadioButton", "^:device", text=_("Partition"),
                tt=_("Use the partition name (/dev/sdb1, etc.)"))
        ui.widget("RadioButton", "^:search", text=_("Search (for larchboot)"),
                tt=_("Test all CD/DVD devices and partitions until the file larch/larchboot is found"))

        ui.widget("Label", ":lm1", text=_("Medium label:"))
        ui.widget("LineEdit", ":labelname", ro=True,
                tt=_("The label that the partition will be given"))
        ui.widget("Button", "^&-:changelabel", text=_("Change"),
                tt=_("Change the label"))

        ui.widget("CheckBox", "^:sessionsave", text=_("Enable session saving"),
                tt=_("If checked, the medium will have the file 'larch/save'"))

        ui.widget("Frame", ":bootloader", text=_("Bootloader"),
                tt=_("You can choose between GRUB and syslinux/isolinux as bootloader"))
        ui.widget("RadioButton", "^:grub", text="GRUB",
                tt=_("Use GRUB as bootloader"))
        ui.widget("RadioButton", "^:syslinux", text="syslinux/isolinux",
                tt=_("Use syslinux (partition) or isolinux (CD/DVD) as bootloader"))
        ui.widget("RadioButton", "^:none", text=_("None"),
                tt=_("Don't install a bootloader (you'll need to provide some means of booting)"))

        ui.widget("CheckBox", ":larchboot", text=_("Bootable via search"),
                tt=_("Create the file larch/larchboot to mark the medium as a bootable larch system"))

        ui.widget("Button", "^:bootlines", text=_("Edit boot entries"),
                tt=_("Edit the file determining the boot entries"))
        ui.widget("Button", "^:grubtemplate", text=_("Edit grub template"),
                tt=_("Edit grub template"))
        ui.widget("Button", "^:syslinuxtemplate", text=_("Edit syslinux/isolinux template"),
                tt=_("Edit syslinux/isolinux template"))

        ui.widget("Button", "^&-:bootcd", text=_("Create boot iso"),
                tt=_("Create a small boot iso for this system (for machines that can't boot from USB)"))
        ui.widget("Button", "^&-:make", text=_("Create larch medium"),
                tt=_("Create the larch iso or set up the chosen partition"))

        ui.widget("Button", "^:cdroot", text=_("Edit cd-root\n(open in file browser)"),
                tt=_("Open a file browser on the profile's 'cd-root' folder"))

        ui.layout(":page_medium", ["*VBOX*",
                ["*HBOX*", ["*VBOX*", ":mediumtype", "*SPACE"], ["*VBOX*",
                    ":bootloader", "*SPACE", ":cdroot"]],
                ["*HBOX*", ":bootlines", ":grubtemplate", ":syslinuxtemplate"],
                "*HLINE", ["*HBOX*", "*SPACE", "&-:make"]])
        ui.layout(":medium_iso", ["*VBOX*", "*SPACE", ":lmiso", "*SPACE"])
        ui.layout(":medium_partition", ["*VBOX*",
                ["*HBOX*", ":lm2", ":larchpart", "&-:selectpart", ":noformat"],
                ["*HBOX*", ":detection", ["*VBOX*",
                    ":sessionsave", ":larchboot", "&-:bootcd"]]])
        ui.layout(":detection", ["*VBOX*", ["*GRID*",
                ["*+*", ":device", ":uuid"],
                ["*+*", ":label", ":search"]],
                ["*HBOX*", ":lm1", ":labelname", "&-:changelabel"]])
        ui.layout(":bootloader", ["*VBOX*", ":grub", ":syslinux",
                "*HLINE", ":none"])

        self.mediumbuilder = Medium()

        # Partition selection popup
        ui.widget("Dialog",  "parts", title=_("Choose Partition"),
                icon="images/larchicon.png")
        ui.widget("Label", "parts:label", text=_("BE CAREFUL - if you select the wrong\n"
                "   partition you might well destroy your system!"
                "\n\nSelect the partition to receive the larch system:"))
        ui.widget("ListChoice", "^parts:list")
        ui.widget("DialogButtons", "parts:buttons", buttons=("Save", "Discard"), dialog="parts")
        ui.layout("parts", ["*VBOX*", "parts:label", "parts:list", "parts:buttons"])
        ui.addslot("parts:list*changed", self.part_selected)


    def setup(self):
        """Set up the build page widget.
        """
        self.profile = config.get("profile")

        part = 1 if config.get("medium_iso") == "" else 0
        ui.command(":mediumtype.set", part)
        self.partition_toggled(part)

        btldr = config.get("medium_btldr")

        ui.command(":%s.set" % btldr, True)

        search = config.get("medium_search")
        ui.command(":%s.set" % search, True)
        ui.command(":larchboot.set", search == "search")

        ui.command(":labelname.x__text", config.get("medium_label"))
        ui.command(":larchpart.x__text")

        ui.command(":sessionsave.set", not os.path.isfile(self.profile
                + "/nosave"))


    def search_toggled(self, on):
        ui.command(":larchboot.set", on)
        _medium_search("search", on)

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


    def selectpart(self):
        # Present a list of available partitions (only unmounted ones
        # are included)
        self.partlist = [_("None")] + command.get_partitions()
        ui.command("parts:list.set", self.partlist)
        self.parts_choice = ""
        if ui.ask("parts.showmodal"):
            ui.command(":larchpart.x__text", self.parts_choice)


    def part_selected(self, i):
        if i <= 0:
            self.parts_choice = ""
        else:
            self.parts_choice = self.partlist[i].split()[0]


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
        command.edit(mld + "/isolinux.cfg", f0,
                label=_("Editing syslinux/isolinux template"))


    def changelabel(self):
        ok, text = ui.ask("textLineDialog",
                _("Enter new label for the boot medium:"),
                None, config.get("medium_label"))
        if ok:
            self.new_label(text)


    def new_label(self, text):
        text = text.strip().replace(" ", "_")
        config.set("medium_label", text)
        ui.command(":labelname.x__text", text)


    def makedevice(self):
        self.makelive(config.get("medium_iso") != "",
                ui.ask(":larchpart.get"),
                not ui.ask(":noformat.active"),
                ui.ask(":larchboot.active"))


    def cdroot(self):
        path = config.get("profile") + "/cd-root"
        if not os.path.isdir(path):
            os.mkdir(path)
        command.browser(path)


    def sessionsaving(self, on):
        """This is a bit weird - the presence of a 'nosave' file in the
        profile means the medium will not get a 'larch/save' file, thus
        disabling session saving.
        """
        sf = self.profile + "/nosave"
        if on:
            if os.path.isfile(sf):
                os.remove(sf)
        elif not os.path.isfile(sf):
            fh = open(sf, "w")
            fh.write("Disable session saving\n")
            fh.close()


    def makelive(self, iso, device, format, larchboot):
        btype = config.get("medium_btldr")  # "grub" / "syslinux" / "none"
        if btype == "grub":
            btype = "boot"
        elif btype == "none":
            btype = ""
        elif iso:
            btype = "isolinux"

        if iso:
            device = ""
            label = ""
            partsel = ""
            format = False
            larchboot = True
        else:
            if not device:
                config_error(_("No partition selected for larch"))
                return

            label = config.get("medium_label")
            partsel = config.get("medium_search")
            # "search" / "uuid" / "label" / "device"
            if partsel == "search":
                partsel = ""
            elif partsel == "device":
                partsel = "partition"

        command.worker(self.mediumbuilder.make, btype, device, label, partsel,
                format, larchboot)
        # btype is "boot" (grub), "syslinux", "isolinux" or "" (no bootloader)
        # For cd/dvd (iso), device is ""
        # partsel = "uuid", "label", "partition", or ""


    def makebootiso(self):
        device = ui.ask(":larchpart.get")
        if device:
            self.bootiso(device)
        else:
            config_error(_("The partition containing the larch live system"
                    "\nmust be specifed."))


    def bootiso(self, device):
        command.worker(self.mediumbuilder.mkbootiso, device)


def _medium_search(stype, on):
    if on:
        config.set("medium_search", stype)

def _medium_btldr(btype, on):
    if on:
        config.set("medium_btldr", btype)
