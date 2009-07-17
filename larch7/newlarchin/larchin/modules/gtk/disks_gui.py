# disks_gui.py - gui toolkit specific methods for the disks stage
#
# (c) Copyright 2009 Michael Towers <gradgrind[at]online[dot]de>
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
# 2009.03.20

import gtk

class gui_disks:
    def __init__(self):


# "checkManupart"
# "liststoreDisks"




# This is all just from the ntfs page ...

        self.checkNTFSdelete = mainWindow.widget("checkNTFSdelete")
        self.checkNTFSdelete.connect("toggled", self.del_check_cb)
        self.checkNTFSshrink = mainWindow.widget("checkNTFSshrink")
        self.checkNTFSshrink.connect("toggled", self.shrink_check_cb)

        self.shrinkwidget = mainWindow.widget("frameNTFSsize")
        self.ntfsadj = mainWindow.widget("adjustmentNTFS")
        self.ntfsadj.connect("value_changed", self.ntfs_size_cb)

        mainWindow.widget("comboboxNTFSdisk").connect("changed",
                self.changedisk_cb)
        self.disklist = mainWindow.widget("liststoreNTFSdisk")
        self.disksize = mainWindow.widget("entryNTFScapacity")
        self.ntfslist = mainWindow.widget("liststoreNTFS")
        self.pselection = mainWindow.widget("listNTFS").get_selection()
        self.sizewidget = mainWindow.widget("entryNTFSfree")


    def del_check_cb(self, widget, data=None):
        state = not self.checkNTFSdelete.get_active()
        self.checkNTFSdelete.set_active(state)
        if state:
            self.checkNTFSshrink.set_sensitive(False)
            self.shrinkwidget.set_sensitive(False)
        elif not self.toofull:
            # Enable the shrinking stuff if shrinking is possible
            self.checkNTFSshrink.set_sensitive(True)
            if self.checkNTFSshrink.get_active():
                self.shrinkwidget.set_sensitive(True)
        # Update free size display
        self.ntfs_size_cb()


    def shrink_check_cb(self, widget, data=None):
        state = not self.checkNTFSshrink.get_active()
        self.checkNTFSshrink.set_active(state)
        self.shrinkwidget.set_sensitive(state)
        # Update free size display
        self.ntfs_size_cb()


    def ntfs_size_cb(self, widget=None, data=None):
        """Update the potential free size display.
        """
        self.sizewidget.set_text(self.get_rest_size_cb())


    def changedisk_cb(self, widget, data=None):
        """When a new drive is selected call the set-up method, set_device_cb.
        """
        active = combobox.get_active()
        if active >= 0:
            self.set_device_cb(self.disklist[active][0])


    def gui_reset(self, drives):
        self.disklist.clear()
        self.ntfslist.clear()
        for d in drives:
            self.disklist.append([d])


    def gui_show_disksize(self, sizetext):
        self.disksize.set_text(sizetext)


    def gui_show_parts(self, plist):
        for p, s in plist:
            self.ntfslist.append([p, "%s GB" % s])
        self.pselection.select_path("0")


    def gui_shrinkinit(self, shrinkon, sizeG):
        self.ntfsadj.lower = self.minsizeG
        self.ntfsadj.upper = self.maxsizeG
        self.ntfsadj.value = sizeG
        # Update free size display (may be superfluous)
        self.ntfs_size_cb()

        self.checkNTFSshrink.set_active(shrinkon)
        if self.gui_deleteflag():
            self.shrinkwidget.set_sensitive(False)
            self.checkNTFSshrink.set_sensitive(False)
        else:
            self.shrinkwidget.set_sensitive(shrinkon)
            self.checkNTFSshrink.set_sensitive(True)


    def gui_set_delete(state):
        self.checkNTFSdelete.set_active(state)


    def gui_deleteflag(self):
        return self.checkNTFSdelete.get_active()


    def gui_shrinkflag(self):
        return self.checkNTFSshrink.get_active()


    def gui_size(self):
        return self.ntfsadj.value
