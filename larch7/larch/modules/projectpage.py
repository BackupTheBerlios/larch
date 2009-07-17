#!/usr/bin/env python
#
# projectpage.py
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
# 2009.06.30

import os


class ProjectPage:
    """This class manages the page dealing with project settings.
    """
    def connect(self):
        return [
                (":choose_profile_combo*changed", self.switch_profile),
                (":profile_rename*clicked", self.get_new_profile_name),
                (":profile_browse*clicked", self.new_profile),
                (":profile_delete*clicked", self.delete_profile),
                (":installation_path_change*clicked", self.get_new_installation_path),
                (":choose_project_combo*changed", self.switch_project),
                (":new_project*clicked", self.get_new_project_name),
                (":project_delete*clicked", self.delete_project),
            ]

    def __init__(self):
        pass


    def setup(self):
        """Set up the project page widget.
        The widget needs config.get("install_path").
        It also needs the list of available profiles (got from listing the
        dirs in the profiles folder in the working directory -
        config.working_dir) and the currently selected profile -
        config.get("profile").
        It needs the list of available projects - config.getsections().
        Also the currently selected project name is needed - config.project.
        """
        self.installpath = config.get("install_path")
        self.profiles = os.listdir(config.profile_dir)
        self.profile = config.get("profile")
        pdn = os.path.dirname(self.profile)
        self.profilename = os.path.basename(self.profile)
        if pdn != config.profile_dir:
            larch_error(_("Profile directory mismatch: '%s' vs. '%s'") %
                    (pdn, config.profile_dir))
            self.profile = config.defaultprofile()
        elif self.profilename not in self.profiles:
            #config_error(_("Profile '%s' doesn't exist") % self.profile)
            self.profile = config.defaultprofile()
            self.profilename = os.path.basename(self.profile)
        config.set("profile", self.profile)
        self.projects = config.getsections()
        self.projects.sort()
        self.project = config.project

        command.ui(":choose_profile_combo.set", self.profiles,
                self.profiles.index(self.profilename))
        command.ui(":choose_project_combo.set", self.projects,
                self.projects.index(self.project))
        command.ui(":installation_path_show.set", self.installpath)
        command.ui(":notebook.setTabEnabled", 1, self.installpath != "/")


    def switch_profile(self, index):
        """This has no effect on the display!
        It is assumed that the display is already updated, or will be
        updated later, and that the index is valid, so that the operation
        cannot fail.
        """
        self.profile = config.profile_dir + "/" + self.profiles[index]
        config.set("profile", self.profile)


    def new_profile(self):
        ok, source, name = command.uiask("specialFileDialog",
                _("Select profile source folder and enter new name"),
                config.profile_dir, _("New name:"),
                (config.profile_dir, base_dir + "/profiles",
                config.current_dir, config.home_dir))
        if ok:
            profile = config.copyprofile(name, source)
            if profile:
                config.set("profile", profile)
                self.setup()


#TODO: There's a problem when renaming a profile that is used by another
# project! I think I've stopped it crashing now, but keep an eye on it.
# When a project's profile doesn't exist it gets set to the default one,
# which is copied over if necessary.
    def get_new_profile_name(self):
        ok, new = command.uiask("textLineDialog",
                _("Enter new name for current profile:"),
                None, self.profilename)
        if ok:
            config.renameprofile(new)
            self.setup()


    def delete_profile(self):
        if command.uiask("confirmDialog",
                _("Do you really want to delete profile '%s'?") % self.profile):
            config.deleteprofile(self.profile)
            self.setup()


    def get_new_installation_path(self):
        # Is anything more necessary? Do I need to test or create the path?
        # I don't think so, the installation code does that.
        # If the path is "/", the installation page should be inhibited,
        # but that is handled by 'setup'.
        ok, path = command.uiask("textLineDialog",
                _("Enter new installation path:"),
                None, self.installpath)
        if ok:
            path = path.strip().rstrip("/")
            if path == "":
                path = "/"
            self.installpath = path
            config.set("install_path", path)
            self.setup()


    def switch_project(self, index):
        config.setproject(self.projects[index])
        self.setup()


    def get_new_project_name(self):
        ok, new = command.uiask("textLineDialog",
                _("Enter name for new project:"),
                None, self.project)
        if ok:
            config.setproject(new)
            self.setup()


    def delete_project(self):
        if len(self.projects) < 2:
            command.uiask("infoDialog",
                    _("Can't delete the only existing project."))
        else:
            config.deleteproject(self.project)
            self.setup()
