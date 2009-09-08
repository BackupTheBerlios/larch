#!/usr/bin/env python
#
# backend.py
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
# 2009.09.08

"""This module handles the running of shell code as root. All of the actual
larch system building work is done via this interface, as the main process
will normally be running as a non-root user and thus not have the necessary
access privileges.  Threads are used to avoid communication problems
which might arise with blocking operations. The 'supershell' operations
are spawned by a thread of the root process.
"""

import os, sys
from subprocess import Popen, PIPE, STDOUT
import threading
from Queue import Queue


def larchroot():
    supershell = Supershell()

    # Start thread to read input from stdin
    mthread = threading.Thread(target=mtstart, args=())
    mthread.start()

    while True:
        line = commqueue.get()

        code, text = line.split(":", 1)
        if code[0] == "X":
            sys.stdout.write(text)
            sys.stdout.flush()

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
                break

        else:
            errout("BUG, bad message: '%s'" % line)


def mtstart():
        """A thread function for reading input from stdin line by
        line. The lines are placed in the communication queue.
        """
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            # Pass on the output of the process
            commqueue.put("M:" + line)
            if line.startswith("/"):
                return

        errout("ERROR: input stream dried up.\n")


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


def errout(text, quit=0):
    sys.stderr.write(text)
    sys.stderr.flush()
    if quit:
        sys.exit(quit)


if __name__ == "__main__":
    if os.getuid() != 0:
        errout("You won't have much fun unless you run this as root!\n\n", 1)

    # This seems to be necessary in command-line mode to stop ctrl-C having
    # a direct effect in this process.
    import signal
    def sigint(num, frame):
        #errout("BACKEND: sigint")
        return
    signal.signal(signal.SIGINT, sigint)

    commqueue = Queue()
    larchroot()

