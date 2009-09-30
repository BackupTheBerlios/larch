# disks.py - discover possible (disk-like) installation devices
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
# 2009.09.29


doc = _("""
<p>This installation program concentrates on just the most essential aspects
of Arch Linux system installation: disk preparation, copying of the system
data, generation of the initramfs, setting up the GRUB bootloader and setting
the root password.
</p>
<p>The remaining configuration of the system can be performed before running
this program. This is one advantage of installing from a 'live' system -
the configuration can be set up and tested before installation.
</p>
<p>Configuration can of course also be performed later, on the running installed
system, if you prefer.
</p>
<p>Simple graphical programs for setting the xorg keyboard layout (xkmap),
for adding users (luser) and for setting the locale (localed) are available
in the larch repository, and may be found in the 'system' category of the
menu if they have been installed.
</p>
<p>Other useful sources of information concerning installation are the Arch
Linux Installation Guide, and the Arch Linux wiki, for example the Beginner's
Guide.
</p>
<p>Click on the 'OK' button to start and, subsequently, to progress from one
stage to the next.
</p>""")

class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&welcome&", self.select_page),
            ]

    def __init__(self, index):
        self.page_index = index

    def setup(self):
        return

    def select_page(self):
        command.pageswitch(self.page_index)


    def init(self):
        return


    def ok(self):
        command.runsignal("&device-select&")

