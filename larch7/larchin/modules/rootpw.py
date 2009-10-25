# rootpw.py - set root password
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
# 2009.10.25


doc = _("""
<h2>Set the Administrator ('root') password</h2>
<p>You should enter a hard-to-guess password for the administrator account
on the newly installed system. Use a mixture of letters, digits and other
characters. The password may be left empty, but that will make it more
difficult to make use of the root account for system administration.
</p>
<p>If you are not a linux expert you are strongly advised not to
lose/forget the password you set here.
</p>""")


class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&passwd!", self.select_page),
                ("&rootpw&", self.rootpw),
            ]

    def __init__(self, index):
        self.page_index = index
        ui.newwidget("Label", "passwd:pwrl", image="images/root.png")
        ui.newwidget("Label", "passwd:pw1l",
                text=_("Enter new password:"))
        ui.newwidget("LineEdit", "passwd:pw1", pw="+")
        ui.newwidget("Label", "passwd:pw2l",
                text=_("Repeat new password:"))
        ui.newwidget("LineEdit", "passwd:pw2", pw="+")

        ui.layout("page:passwd", ["*VBOX*",
                ["*HBOX*", "passwd:pwrl",
                    ["*VBOX*", "*SPACE",
                        ["*GRID*",
                            ["*+*", "passwd:pw1l", "passwd:pw1"],
                            ["*+*", "passwd:pw2l", "passwd:pw2"]
                        ]
                    ]],
                "*SPACE"])

    def setup(self):
        return


    def select_page(self, init):
        command.pageswitch(self.page_index, _("Set Root Password"))


    def init(self):
        self.pw1 = ""
        self.pw2 = ""
        ui.command("passwd:pw1.x__text", self.pw1)
        ui.command("passwd:pw2.x__text", self.pw2)


    def ok(self):
        command.runsignal("&rootpw&")


    def rootpw(self):
        pw = ui.ask("passwd:pw1.get")
        if pw != ui.ask("passwd:pw2.get"):
            ui.infoDialog(_("The passwords are not identical,\n"
                    "  Please try again."))
            return

        # Set the password
        if backend.set_pw(pw):
            command.runsignal("&grub!")

