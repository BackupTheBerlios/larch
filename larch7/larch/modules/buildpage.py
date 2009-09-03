#!/usr/bin/env python
#
# buildpage.py
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
# 2009.09.01

from build import Builder
import os


class BuildPage:
    """This class manages the page dealing with larch system building.
    """
    def connect(self):
        return [
                (":build*clicked", self.build),
                (":ssh*toggled", self.sshtoggle),
                (":locales*clicked", self.locales),
                (":rcconf*clicked", self.rcconf),
                (":initcpio*clicked", self.initcpio),
                (":overlay*clicked", self.overlay),
                (":filebrowser*clicked", self.filebrowser),
            ]


    def __init__(self):
        self.builder = Builder()
        self.sshgen = True


    def setup(self):
        """Set up the build page widget.
        """
        self.oldsqf = self.builder.oldsqf_available()
        ui.command(":oldsquash.enable", self.oldsqf)
        ssh = self.builder.ssh_available()
        self.sshgen = ssh and self.sshgen
        ui.command(":ssh.set", self.sshgen)
        ui.command(":ssh.enable", ssh)


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

    def filebrowser(self):
        ok, new = ui.ask("textLineDialog",
                _("Enter new command to open file browser (use '%' as directory argument)"),
                None, config.get("filebrowser"))
        if ok:
            config.set("filebrowser", new)


    def build(self):
        self.builder.build(self.sshgen,
                ui.ask(":oldsquash.active") if self.oldsqf else False)
