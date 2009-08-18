#!/usr/bin/env python
#
# larch.py
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
# 2009.08.18

"""This is the initial module of the larch live-builder program. It should
be started with su or sudo, but in such a way that the environment variable
'USER' is set to the owner of the configuration directory, etc. Thus it is
possible to change the configuration files within larch, preserving the
correct ownership.

To run the user interface and main program as a normal user, a separate
process is spawned, which communicates with the initial (root) process
via pipes. Threads are used to avoid communication problems
which might arise with blocking operations. The 'supershell' operations
are spawned by a thread of the root process.
"""

import os, sys, pwd
from subprocess import Popen, PIPE, STDOUT
import threading
from Queue import Queue

base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
module_dir = "%s/modules" % base_dir
#sys.path.append(module_dir)


def chid():
    """Drop root privileges and reset the home-directory before entering
    the subprocess.
    """
    os.environ["HOME"] = userinfo[2]
    os.setgid(userinfo[1])
    os.setuid(userinfo[0])


def larchroot(uid, gid, home):
    global userinfo, commqueue
    userinfo = [uid, gid, home]
    commqueue = Queue()
    mainprocess = Popen(["%s/main.py" % module_dir] + sys.argv,
            preexec_fn=chid, stdin=PIPE, stdout=PIPE)
    supershell = Supershell()

    # Start thread to read input from the subprocess
    mthread = threading.Thread(target=mtstart, args=(mainprocess, "M"))
    mthread.start()

    while True:
        # Is there a problem if one of the processes dies?

        line = commqueue.get()
        code, text = line.split(":", 1)
        if code[0] == "X":
            mainprocess.stdin.write(text)

        elif code[0] == "M":
            if text[0] == ">":
                # A normal superuser command
                supershell.run(text[1:])
            elif text[0] == ".":
                # If a superuser command is running, kill it
                supershell.kill()
            elif text[0] == "/":
                # Quit requested
                #supershell.kill()
                mainprocess.kill()
                break

        else:
            errout("BUG, bad message: '%s'" % line)
            # exits


    sys.exit(mainprocess.returncode)


def mtstart(process, flag):
        """A thread function for reading input from a subprocess line by
        line. The lines are placed in the communication queue.
        """
        while True:
            line = process.stdout.readline()
            if not line:
                break
            # Pass on the output of the process
            commqueue.put("%s:%s" % (flag, line))

        process.wait()
        commqueue.put("%s:/%d\n" % (flag, process.returncode))


def errout(text, quit=1):
    sys.stderr.write(text)
    if quit:
        sys.exit(quit)


class Supershell:
    """This class handles the execution of shell calls as 'root' user.
    As no privilege-changing mechanism is implemented here this code
    must be run by the root user.
    """
    def __init__(self):
        self.process = None


    def run(self, cmd):
        """Run a shell command in a separate thread.
        """
        self.pthread = threading.Thread(target=self.tstart, args=(cmd,))
        self.pthread.start()


    def tstart(self, cmd):
        """Run a command in a separate process.
        This reads output line by line and passes it on, but it won't
        return until the process has completed, so it should not be called
        from a thread that needs to be reactive.
        """
        self.process = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT,
                universal_newlines=True)
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            # Pass on the output of the process
            commqueue.put("X:-%s\n" % line.rstrip())

        self.process.wait()
        commqueue.put("X:@%d\n" % self.process.returncode)
        self.process = None


    def kill(self):
        """Kill the current subprocess.
        As the 'start' method blocks, this can only be called from the
        main thread.
        """
        if self.process:
            self.process.kill()


if __name__ == "__main__":
    if os.getuid() != 0:
        errout("You won't have much fun unless you run this as root!\n\n", 0)

    pwdinfo = pwd.getpwnam(os.environ["USER"])
    larchroot(pwdinfo[2], pwdinfo[3], pwdinfo[5])
