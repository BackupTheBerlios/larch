# welcome.py - Initial page
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
# 2009.11.06


doc = _("""
<h2><em>larchin</em> - An installer for <em>larch live</em> systems</h2>
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

text = _("""
<p>Welcome to larchin, the easy way to install a ready-configured
Arch Linux.
</p>
<p>With this program you can install a larch live system as a normal
Arch Linux system, retaining its configuration settings.
</p>
<p align="center"><img src="images/larchin.png" width="150" height="150" />
</p>
<p>Press the 'OK' button to progress to the next stage.
</p>
""")

class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&welcome!", self.select_page),
                ("&step1&", self.step1),
            ]

    def __init__(self, index):
        self.page_index = index
        self.run0 = True


    def buildgui(self):
        ui.widget("HtmlView", "page:welcome:l1", html=text)

        ui.layout("page:welcome", ["*VBOX*", "page:welcome:l1"])


    def select_page(self, init):
        if self.run0:
            self.run0 = False
            self.buildgui()

        command.pageswitch(self.page_index, _("Welcome!"))


    def init(self):
        return


    def ok(self):
#debugging
        if "P" in dbg_flags:
            self.plist = [["/", "/dev/sdb5", "ext4"],
                    ["/boot", "/dev/sdb1", "ext2"],
                    ["swap", "/dev/sdb2", ""],
                    ["/home", "/dev/sdb6", "ext4"]]
            parts = ""
            for p in self.plist:
                parts += "\n  " + " : ".join(p)
            ui.confirmDialog("Debugging. Using:" + parts,
                async="&step1&")
            return
#-
        self.step1(False)


    def step1(self, dbg):
        if dbg:
            ui.sendsignal("&install!", self.plist)
        else:
            ui.sendsignal("&device-select!")
