#!/usr/bin/env python
#
# lardm.py   --  Larch Display Manager (for logging into xorg sessions)
#
# (c) Copyright 2009, 2010 Michael Towers (larch42 at googlemail dot com)
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
# 2010.02.27

import os, sys, pwd, spwd, crypt, traceback
from subprocess import call, Popen, PIPE, STDOUT

import lardmgui

# Change to lardm directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))
# Get configuration options
execfile("/etc/lardm.conf")
import __builtin__
__builtin__.theme = theme

import gettext
lang = os.getenv("LANG")
if lang:
    gettext.install('lardm', 'i18n', unicode=1)



class Lardm(lardmgui.LardmGui):
    def __init__(self):
        self.loginuname = None

        self.hostname = Popen("hostname", stdout=PIPE).communicate()[0].strip()
        self.userlist = ["root"] + self.getUsers()

        lardmgui.LardmGui.__init__(self)


    def login(self, user, pw):
        pwcrypt = spwd.getspnam(user)[1]
        if crypt.crypt(pw, pwcrypt) != pwcrypt:
            return _("Wrong password for '%s'") % user
        self.loginuname = user
        return None


    def shutdown(self, stype):
        self.loginuname = stype
        for dn, tty in lardmd_displays:
            p = Popen(["/usr/bin/xdpyinfo", "-display", dn],
                    stdout=PIPE, stderr=STDOUT)
            p.communicate()
            if p.returncode == 0:
                return tty
        return None


    def switch_tty(self, tty):
        self.loginuname = None
        #call(["/usr/bin/chvt", tty[3:]])


    def getUsers(self):
        """Return a list of 'normal' users, i.e. those with a home
        directory in /home and a login shell (ending with 'sh').
        """
        return [u[0] for u in pwd.getpwall()
                if (u[5].startswith('/home/') and u[6].endswith('sh'))]



if __name__ == "__main__":
    try:
        dok = False
        display, user = sys.argv[1].split("_", 1)
        for d, t in lardmd_displays:
            if d == display:
                dok = True
                break
    except:
        pass
    if not dok:
        print "ERROR: No valid DISPLAY passed"
        sys.exit(1)

    os.environ["DISPLAY"] = display
    if os.path.isfile("/etc/X11/xinit/xinitrc.lardm"):
        call(["sh", "/etc/X11/xinit/xinitrc.lardm"])

    if not user:
        lardmgui.init()
        ui = Lardm()
        lardmgui.mainloop(ui)
        user = ui.loginuname
        ui = None

    if user == None:
        sys.exit(1)

    elif user == "shutdown":
        print "shutdown"
        os.execl("/sbin/halt", "halt")

    elif user == "restart":
        print "restart"
        os.execl("/sbin/reboot", "reboot")

    else:
        pwdinfo = pwd.getpwnam(user)
        uid = pwdinfo[2]
        gid = pwdinfo[3]
        homedir = pwdinfo[5]
        shell = pwdinfo[6]
        call(["xauth", "-f", homedir + "/.Xauthority", "generate",
                display, ".", "trusted"])
        os.chown(homedir + "/.Xauthority", uid, gid)

        e = {   "SHELL"     : shell,
                "TERM"      : "xterm",
                "MAIL"      : "/var/spool/mail/" + user,
                "HOME"      : homedir,
                "USER"      : user,
                "LOGNAME"   : user,
                "DISPLAY"   : display,
                "XAUTHORITY": homedir + "/.Xauthority",
            }
        os.chdir(homedir)
        os.setgid(gid)
        os.setuid(uid)

        os.execve("/usr/bin/ck-launch-session",
                ("ck-launch-session", shell, "--login",
                 homedir + "/.xinitrc"), e)

