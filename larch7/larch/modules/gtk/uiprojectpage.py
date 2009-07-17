#!/usr/bin/env python
#
# uibase.py
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
# 2009.06.08

"""This is the gui handler for the project settings page.
"""

import gtk, glib
import os

class UIProjectPage:
    def __init__(self):
        self.signals = {
                "on_cb_profile_changed"         : self._changeprofile,
                "on_b_template_browse_clicked"  : self._getprofile,
                "on_b_rename_profile_clicked"   : self._renameprofile,
                "on_cb_project_changed"         : self._changeproject,
                "on_b_new_project_clicked"      : self._newproject,
                "on_b_install_path_new_clicked" : self._newinstallpath
            }

        builder = gtk.Builder()
        builder.add_from_file(os.path.join(base_dir,
                "modules/gtk/filechooser1.glade"))

        self.installpathwidget = ui.widget("entry_installpath")
        self.profilewidget = ui.widget("cb_profile")
        self.projectwidget = ui.widget("cb_project")
        self.profilelist = ui.widget("ls_profiles")
        self.projectlist = ui.widget("ls_projects")
        self.newprofiledialog = builder.get_object("filechooserdialog1")
        self.newprofilename = builder.get_object("entry_profile")
        self.newprofiledialog.add_shortcut_folder(config.profile_dir)
        self.newprofiledialog.add_shortcut_folder(os.path.join(base_dir,
                "profiles"))
        self.profiledirstart = config.profile_dir


    def setup(self):
        self.installpathwidget.set_text(self.installpath)

        self.block = True

        self.profilelist.clear()
        for item in self.profiles:
            self.profilelist.append([item])
        i = self.profiles.index(self.profilename)
        self.profilewidget.set_active(i)

        self.projectlist.clear()
        for item in self.projects:
            self.projectlist.append([item])
        i = self.projects.index(self.project)
        self.projectwidget.set_active(i)

        ui.add_idle_task(self.unblock)


    def unblock(self, arg):
        self.block = False


    def _changeprofile(self, widget, data=None):
        new = self.profiles[widget.get_active()]
        if new != self.profile:
            self.switch_profile(new)


    def _getprofile(self, widget, data=None):
        self.newprofiledialog.set_current_folder(self.profiledirstart)
        self.newprofilename.set_text("")
        res = self.newprofiledialog.run()
        text = self.newprofilename.get_text()
        self.newprofiledialog.hide()
        if res == 1:
            fpath = self.newprofiledialog.get_filename()
            if not fpath:
                fpath = self.newprofiledialog.get_current_folder()
            self.profiledirstart = os.path.dirname(fpath)
            t = text.strip()
            if not t:
                t = os.path.basename(fpath)
            self.new_profile(fpath, t)


    def _renameprofile(self, widget, data=None):
        new = ui.popup_entrydialog()
        if new:
            self.rename_profile(new.replace(" ", "_"))


    def _changeproject(self, widget, data=None):
        new = self.projects[widget.get_active()]
        if new != self.project and not self.block:
            self.switch_project(new)


    def _newproject(self, widget, data=None):
        new = ui.popup_entrydialog()
        if new:
            self.switch_project(new.replace(" ", "_"))


    def _newinstallpath(self, widget, data=None):
        new = ui.popup_entrydialog()
        if new:
            self.new_installation_path(new.replace(" ", "_"))

