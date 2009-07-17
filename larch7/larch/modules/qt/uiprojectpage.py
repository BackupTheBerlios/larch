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
# 2009.06.09

"""This is the gui handler for the project settings page.
"""

from PyQt4 import QtGui, QtCore
from PyQt4.uic import loadUi
import os

class UIProjectPage:
    def __init__(self):
        ui.connect0(ui.cb_profile, self._changeprofile,
                "currentIndexChanged(const QString &)")
        ui.connect0(ui.b_template, self._getprofile)
        ui.connect0(ui.b_rename_profile, self._renameprofile)
        ui.connect0(ui.cb_project, self._changeproject,
                "currentIndexChanged(const QString &)")
        ui.connect0(ui.b_new_project, self._newproject)
        ui.connect0(ui.b_install_path_new, self._newinstallpath)

        self.newprofiledialog = QtGui.QDialog()
        loadUi(os.path.join(base_dir, "modules/qt/copyprofiledialog.ui"),
                self.newprofiledialog)


        #self.installpathwidget = ui.widget("entry_installpath")
        #self.profilewidget = ui.widget("cb_profile")
        #self.projectwidget = ui.widget("cb_project")
        #self.profilelist = ui.widget("ls_profiles")
        #self.projectlist = ui.widget("ls_projects")
        #self.newprofiledialog = builder.get_object("filechooserdialog1")
        #self.newprofilename = builder.get_object("entry_profile")
        #self.newprofiledialog.add_shortcut_folder(config.profile_dir)
        #self.newprofiledialog.add_shortcut_folder(os.path.join(base_dir,
        #        "profiles"))
        self.profiledirstart = config.profile_dir


    def setup(self):
        self.entry_installpath.setText(self.installpath)

#TODO
        self.block = True

        self.cb_profile.clear()
        self.cb_profile.addItems(self.profiles)
        i = self.profiles.index(self.profilename)
        self.cb_profile.setCurrentIndex(i)

        self.cb_project.clear()
        self.cb_project.addItems(self.projects)
        i = self.projects.index(self.project)
        self.cb_project.setCurrentIndex(i)

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

