#!/usr/bin/env python
#
# command.py
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
# 2009.05.17

"""This module handles the execution of shell calls as 'root' user.
"""

from subprocess import Popen, PIPE, STDOUT
import pexpect          # for running commands as root


class Supershell:
    def __init__(self, cmd, outputmethod=None):
        self.process = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
        self.result = ""
        while True:
            line = self.process.stdout.readline()
            if not line: break
            # Allow the output from this call to be processed line-by-line
            # by a method running in the gui thread.
            if outputmethod:
                mainWindow.idle_call(self.read_output_cb, outputmethod, line)
            self.result += line
            plog(line)

        self.ok = (self.process.returncode == 0)

    def read_output_cb(self, outputmethod, textline):
        """By setting self.outputmethod to a (gui thread) method, the
        output of a supershell command can be processed line-by-line in
        the gui.
        """
        outputmethod(textline)
        return False        # So this method is not repeatedly called


    def rootrun(self, cmd):
        """Run the given command as 'root'.
        Return a pair (completion code, output).
        """
        # If not running as 'root' use pexpect to use 'su' to run the command
        if (os.getuid() == 0):
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
            o = p.communicate()[0]
            return (p.returncode, o)
        else:
            if not self.password:
                pw = popupRootPassword()
                if (pw == None):
                    return (1, _("You cancelled the operation."))
                cc, mess = asroot('true', pw)
                if (cc != 0):
                    return (cc, mess)
                self.password = pw
            return asroot(cmd, self.password)

def asroot(cmd, pw):
    """Run a command as root, using the given password.
    """
    child = pexpect.spawn('su -c "%s"' % cmd)
    child.expect(':')
    child.sendline(pw)
    child.expect(pexpect.EOF)
    o = child.before.strip()
    return (0 if (o == '') else 1, o)


# Something like this?
# su -c 'ls +++ 2>/dev/null; echo "^END^=$?"'
