#!/usr/bin/env python
#
# ldmd.py   --  Larch Display Manager Daemon (for logging into xorg sessions)
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
# 2009.11.19

"""This is the daemon, which waits for messages (via an AF_UNIX socket,
'ldmd').
When a message is received a new xorg session is started with a login
screen.
"""

import sys, os, threading, traceback, signal
from datetime import datetime
from subprocess import call, Popen, PIPE, STDOUT

ldm_dir = os.path.dirname(os.path.realpath(__file__))
# Get configuration for system-dependent paths, etc.

execfile("/etc/ldm.conf")

#import gettext
#lang = os.getenv("LANG")
#if lang:
#    gettext.install('ldm', 'i18n', unicode=1)

from socket import socket, AF_UNIX, SOCK_STREAM

class Ldmd:
    def __init__(self):
        if os.path.isfile(logfile):
            call(["mv", logfile, logfile + ".1"])
        # Create an unbound and not-connected socket.
        self.sock = socket(AF_UNIX, SOCK_STREAM)
        # Bind the socket to 'ldmd' in the abstract namespace.
        # Note the null-byte.
        self.sock.bind("\0ldmd")
        # Create a backlog queue for up to 1 connection.
        self.sock.listen(1)
        self.log("Started\n")
        self.new_session(autouser)


    def wait(self):
        try:
            conn = None
            # Blocks until a connection arrives:
            conn = self.sock.accept()[0]
            # A tuple (connected_socket, None) is returned upon connection.
            # Note we get the first argument and throw away the rest.
            self.log("Connection accepted\n")
            # Say hi
            conn.send("ok\n")

            # Wait for response
            msg = conn.recv(64)
            if msg and (msg.strip() == "NEW"):
                if self.new_session():
                    conn.send("done\n")

        except:
            self.log("".join(traceback.format_exc()))

        if conn:
            # Close the connection.
            # This will unblock the other peer in case it's waiting for
            # another message.
            self.log("Closing connection\n")
            conn.close()


    def new_session(self, user=""):
        # Determine which display to use
        # Look for a free display/tty pair
        display = None
        for dn, tty in ldmd_displays:
            p = Popen(["/usr/bin/xdpyinfo", "-display", dn],
                    stdout=PIPE, stderr=STDOUT)
            p.communicate()
            if p.returncode == 1:
                p = Popen(["/usr/bin/pgrep", "-t", tty],
                        stdout=PIPE, stderr=STDOUT)
                p.communicate()
                if p.returncode == 1:
                    display = dn
                    break
        if not display:
            self.log("*** Couldn't open display\n")
            return False
        t = threading.Thread(target=self.start_session,
                args=(display, tty, user))
        t.start()
        return True


    def start_session(self, display, tty, user):
        # Start new session
        process = Popen(["/usr/bin/xinit", ldm_dir + "/ldm.py",
                (display + "!" + user),
                "--", "/usr/bin/X", display, tty, "-nolisten", "tcp"],
                stdout=PIPE, stderr=STDOUT)
        displays.append(tty)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            self.log(display + "]" + line)
        displays.remove(tty)
        if displays:
            call(["/usr/bin/chvt", displays[-1][3:]])
        else:
            self.new_session()


    def log(self, line):
        fh = open(logfile, "a")
        ts = datetime.now().strftime("%Y-%m-%d/%H:%M:%S[")
        fh.write(ts + line)
        fh.close()


def tidy(type, value, tb):
    ldmd.log("Trap:\n" +
            "".join(traceback.format_exception(type, value, tb)))
    end()

def end(*args):
    ldmd.log("Killing displays\n")
    for tty in displays:
        call(["pkill", "-t", tty])
    ldmd.log("Exiting\n")
    os._exit(1)

sys.excepthook = tidy
signal.signal(signal.SIGTERM, end)
#signal.signal(signal.SIGKILL, end) - doesn't work


if __name__ == "__main__":
    displays = []
    ldmd = Ldmd()
    fh = open("/var/run/ldmd.pid", "w")
    fh.write("%d\n" % os.getpid())
    fh.close()
    while True:
        ldmd.wait()


