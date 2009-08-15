#!/usr/bin/env python
#
# installpage.py
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
# 2009.08.15

import os, shutil
from installation import Installation, pacmanoptions

#TODO: remove (just for testing)
#import sys


class InstallPage:
    """This class manages the page dealing with Arch installation.
    """
    def connect(self):
        return [
                (":addedpacks*clicked", self.edit_addedpacks),
                (":baseveto*clicked", self.edit_baseveto),
                (":pacmanconf*clicked", self.edit_pacmanconf),
                (":repos*clicked", self.edit_repos),
                (":mirrorlist_change*clicked", self.edit_mirrorlist),
                (":mirrorlist*toggled", self.toggle_mirrorlist),
                (":use_local_mirror*toggled", self.toggle_local_mirror),
                (":local_mirror_change*clicked", self.new_local_mirror_path),
                (":cache_change*clicked", self.new_cache_path),
                (":sync*clicked", self.dosync),
                (":update*clicked", self.doupdate),
                (":add*clicked", self.doadd),
                (":remove*clicked", self.doremove),
                (":install*clicked", self.installation.install),
            ]


    def __init__(self):
        self.installation = Installation()


    def setup(self):
        """Set up the installation page widget.
        """
        self.profile = config.get("profile")
        command.ui(":cache_show.set", config.get("pacman_cache"))

        if config.get("usemirrorlist"):
            command.ui(":mirrorlist.enable", True)
        if config.get("uselocalmirror"):
            command.ui(":use_local_mirror.enable", True)
        command.ui(":local_mirror.set", config.get("localmirror"))


    def edit_addedpacks(self):
        command.edit("addedpacks")

    def edit_baseveto(self):
        command.edit("baseveto", "")

    def edit_pacmanconf(self):
        command.edit("pacman.conf.options",
                os.path.join(base_dir, "data", "pacman.conf"),
                label=_("Editing pacman.conf options only"),
                filter=pacmanoptions)

    def edit_repos(self):
        command.edit("pacman.conf.larch",
                os.path.join(base_dir, "data", "pacman.conf.larch"),
                label=_("Editing pacman.conf repositories only"))

    def edit_mirrorlist(self):
        f = os.path.join(config.working_dir, "mirrorlist")
        fi = "/etc/pacman.d/mirrorlist"
        if not os.path.isfile(fi):
            fi = os.path.join(base_dir, "data", "mirrorlist.%s" %
                    config.get("platform"))
        command.edit(f, fi, label=_("Editing mirrorlist: Uncomment ONE entry"))


    def toggle_mirrorlist(self, on):
        config.set("usemirrorlist", "yes" if on else "")


    def toggle_local_mirror(self, on):
        config.set("uselocalmirror", "yes" if on else "")


    def new_local_mirror_path(self):
        # Is anything more necessary? Do I need to test the path?
        # Would a directory browser be better?
        ok, path = command.uiask("textLineDialog",
                _("Enter new local mirror path:"),
                None, config.get("localmirror"))
        if ok:
            path = path.strip().rstrip("/")
            config.set("localmirror", path)
            command.ui(":local_mirror.set", path)


    def new_cache_path(self):
        # Is anything more necessary? Do I need to test the path?
        # Would a directory browser be better?
        ok, path = command.uiask("textLineDialog",
                _("Enter new package cache path:"),
                None, config.get("pacman_cache"))
        if ok:
            path = path.strip().rstrip("/")
            config.set("pacman_cache", path)
            command.ui(":cache_show.set", path)


    def dosync(self):
        command.NYI()


    def doupdate(self):
        command.NYI()


    def doadd(self):
        command.NYI()


    def doremove(self):
        command.NYI()
