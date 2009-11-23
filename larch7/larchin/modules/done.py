# done.py - The final page, installation completed
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

text = _("""
<h2>That just about wraps it up for now, folks!</h2>
<p>You should now have successfully installed <em>Arch Linux</em> on your
computer, and if you set up GRUB correctly it should be possible to
reboot into the new system.
</p>
<p>Of course nobody is perfect, and certainly no computer program or
computer programmer is, so you might be the unlucky one for whom it
didn't work. If so, please post a bug report.
</p>
<p>And remember: Share and Enjoy!
</p>""")

doc = _("""
<h2>The End</h2>
<p>What do you expect here?
</p>""")

import time, re


class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
#TODO: the tweaks page has yet to be written
                ("&tweaks!", self.select_page),
            ]

    def __init__(self, index):
        self.page_index = index
        self.run0 = True


    def buildgui(self):
        ui.widget("HtmlView", "done:view", html=text)
        ui.layout("page:done", ["*VBOX*", "done:view"])


    def select_page(self, init):
        if self.run0:
            self.run0 = False
            self.buildgui()

        command.pageswitch(self.page_index, _("Installation Complete"))


    def init(self):
        return

    def ok(self):
        ui.sendsignal("$$$uiquit$$$")
