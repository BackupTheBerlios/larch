#!/usr/bin/env python
#
# xkmap.py   --  Simple GUI for xorg keymap setting with evdev and 'setxkbmap'
#
# (c) Copyright 2009 Michael Towers (larch42 at googlemail dot com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#-------------------------------------------------------------------
# 2009.11.23

import os, sys, threading, traceback
from uipi import Uipi
from xkmap_base import Xkmap

# Get xkmap directory
thisdir = os.path.dirname(os.path.realpath(__file__))
# Get configuration for system-dependent paths, etc.
execfile(thisdir + '/xkmap.conf')

import gettext
t = gettext.translation('xkmap', thisdir + '/i18n', fallback=True)
_ = t.ugettext


doc = _("""
<h2><em>xkmap</em></h2>
<p><strong> - a simple gui front-end for <em>evdev</em> and <em>setxkbmap</em></strong>
</p>
<p>This utility allows you to set the keyboard mapping for the <em>xorg</em>
windowing system. It was designed for <em>larch live</em> systems (based on
Archlinux) but may work on other GNU/Linux systems.
</p>
<p>To keep it simple not all the options which are available for keyboard
configuration may be set by this utility, it just allows setting of the
basic layouts and variants (as found in the ..../xkb/rules/base.lst file).
</p>
<p><em>xorg</em> keymaps can be set immediately, and just for the present
session, by clicking 'Set temporarily for this user'. It is also possible
to make the settings here permanent, either on a global level (for all
users) or just for the current user, but as the mechanism
for doing this is dependent on the configuration of the underlying
system, it cannot be guaranteed that this will work for you.
</p>
<p>A global keymap can be set by configuring the 'evdev' keyboard driver
or the 'larch display manager' (<em>ldm</em>). To make global changes
you must be running <em>xkmap</em> as root, or else enter the root
password when prompted.
</p>
<p>Setting a persistent keymap for just the present user (overriding any
global keymap) is possible if the file .xinitrc in the user's home
directory is sourced during xorg session start.
</p>
<p>The configuration file may need adjusting for
non-<em>Arch</em> distributions.
</p>
<p>'Quit' exits without making any (further) changes.
</p>
<br />
<p>This program was written for the <em>larch</em> project:
http://larch.berlios.de
</p>
<p>It is free software, released under the
<strong>GNU General Public License</strong>.
</p>
<p>(c) 2009 Michael Towers
</p>""")


STANDARDLAYOUT = ("-", "Standard")

class Wrapper(Uipi):
    def __init__(self):
        Uipi.__init__(self)


    def gui(self):
        self.widget("Window", "xkmap", title="xkmap", #size="400_300",
                icon="xkmap.png")
        # - Header
        self.widget("Label", "header_l",
                html=_("<h1>Set Keyboard Map (Language)</h1>"))

        # Stack, to share area with
        self.widget("Stack", "stack", pages=["main", "docs"])

        # Setter buttons
        self.widget("Button", "^&-settemp",
                text=_("Set temporarily for this user"))
        self.widget("Button", "^&-setuser",
                text=_("Set permanently for this user"))
        self.widget("Button", "^&-clearuser",
                text=_("Clear user's override setting\n - use global setting"))
        self.widget("Button", "^&-setglobal",
                text=_("Set permanently for all users"))

        # Quit button
        self.widget("Button", "^quit", text=_("Quit"))

        # Doc viewer
        self.widget("Button", "^showdocs", text=_("Help"))
        self.widget("HtmlView", "docview", html=doc)
        self.widget("Button", "^docexit", text=_("Hide docs"))

        self.xkmap = Xkmap(self)
        self.xkmap.buildgui()

        self.layout("xkmap", ["*VBOX*", "header_l", "stack"])
        self.layout("main", ["*VBOX*", "xkmap:frame",
                ["*HBOX*",
                    ["*VBOX*", "*SPACE", "&-clearuser"],
                    ["*VBOX*", "&-settemp", "&-setuser", "&-setglobal"]],
                ["*HBOX*", "showdocs", "*SPACE", "quit"]])
        self.layout("docs", ["*VBOX*",
                "docview",
                ["*HBOX*", "*SPACE", "docexit"]])

        self.xkmap.init()
        self.command("xkmap.setVisible", True)

        self.addslot("&-setglobal*clicked", self.xkmap.setSys)
        self.addslot("&-settemp*clicked", self.xkmap.setNow)
        self.addslot("&-setuser*clicked", self.xkmap.setUser)
        self.addslot("&-clearuser*clicked", self.xkmap.clearUser)
        self.addslot("quit*clicked", self.quit)
        self.addslot("docexit*clicked", self._hidedocs)
        self.addslot("showdocs*clicked", self._showdocs)

        self.setDisableWidgets("xkmap", ("xkmap",))


    def _showdocs(self):
        self.command("stack.set", 1)


    def _hidedocs(self):
        self.command("stack.set", 0)



if __name__ == "__main__":
    ui = Wrapper()
    ui.gui()
    sys.exit(ui.mainloop())
