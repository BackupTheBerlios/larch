#!/usr/bin/env python
#
# buildpage.py
#
# (c) Copyright 2009-2010 Michael Towers (larch42 at googlemail dot com)
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
# 2010.02.12

from build import Builder
import os


class BuildPage:
    """This class manages the page dealing with larch system building.
    """
    def connect(self):
        return [
                ("&-:build*clicked", self.build),
                (":ssh*toggled", self.sshtoggle),
                (":locales*clicked", self.locales),
                (":rcconf*clicked", self.rcconf),
                (":initcpio*clicked", self.initcpio),
                (":overlay*clicked", self.overlay),
                ("&larchify&", self.larchify),
            ]


    def __init__(self):
        ui.widget("Label", ":larchify",
                text=_("The system to be compressed must be installed and ready."))
        ui.widget("Button", "^:locales", text=_("Edit supported locales"),
                tt=_("Edit the /etc/locale.gen file to select supported glibc locales"))
        ui.widget("Button", "^:rcconf", text=_("Edit Arch configuration file (/etc/rc.conf)"),
                tt=_("Edit the /etc/rc.conf file to configure the live system"))
        ui.widget("OptionalFrame", ":larchify_advanced",
                text=_("Advanced Options"))
        ui.widget("Button", "^:initcpio", text=_("Edit mkinitcpio.conf"),
                tt=_("Edit the configuration file for generating the initramfs via mkinitcpio"))
        ui.widget("Button", "^:overlay", text=_("Edit overlay (open in file browser)"),
                tt=_("Open a file browser on the profile's 'rootoverlay'"))
        ui.widget("CheckBox", "^:ssh", text=_("Generate ssh keys"),
                tt=_("Enables pre-generation of ssh keys"))
        ui.widget("CheckBox", ":oldsquash", text=_("Reuse existing system.sqf"),
                tt=_("Reuse existing system.sqf, to save time if the base system hasn't changed"))
        ui.widget("Button", "^&-:build", text=_("Larchify"),
                tt=_("Build the main components of the larch system"))

        ui.layout(":page_larchify", ["*VBOX*", ":larchify", "*SPACE",
                ["*HBOX*", ":locales", "*SPACE", ":rcconf"], "*SPACE",
                ":larchify_advanced", ["*HBOX*", "*SPACE", "&-:build"]])
        ui.layout(":larchify_advanced", ["*HBOX*",
                ["*VBOX*", ":initcpio", ":overlay"], "*SPACE",
                ["*VBOX*", ":ssh", "*SPACE", ":oldsquash"]])

        self.builder = Builder()
        self.sshgen = True


    def setup(self):
        """Set up the build page widget.
        """
        idir = config.ipath()
        if not os.path.isdir(idir + "/var/lib/pacman/local"):
            config_error(_("No Arch installation at %s") % idir)
            return False
        ui.command(":oldsquash.enable", self.builder.oldsqf_available())
        ssh = self.builder.ssh_available()
        self.sshgen = ssh and self.sshgen
        ui.command(":ssh.set", self.sshgen)
        ui.command(":ssh.enable", ssh)
#TODO: Remove hack if the underlying bug gets fixed
        # A hack to overcome a bug (?) in (py)qt
        ui.command(":larchify_advanced.enable_hack")
        return True

    def sshtoggle(self, on):
        self.sshgen = on

    def locales(self):
        command.edit("rootoverlay/etc/locale.gen",
                config.ipath("etc/locale.gen"))

    def rcconf(self):
        command.edit("rootoverlay/etc/rc.conf", config.ipath("etc/rc.conf"))

    def initcpio(self):
        command.edit("rootoverlay/etc/mkinitcpio.conf.larch0",
                config.ipath("etc/mkinitcpio.conf.larch0"))

    def overlay(self):
        path = config.get("profile") + "/rootoverlay"
        if not os.path.isdir(path):
            os.mkdir(path)
        command.browser(path)

    def build(self):
        self.larchify(self.sshgen, ui.ask(":oldsquash.active"))


    def larchify(self, sshkeys, oldsquash):
        command.worker(self.builder.build,
                self.builder.ssh_available() and sshkeys,
                self.builder.oldsqf_available() and oldsquash)

