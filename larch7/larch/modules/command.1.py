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
# 2009.05.18

"""This module handles the execution of shell calls as 'root' user.
As no privilege-changing mechanism is implemented here the code in this
module must be run by the root user.
"""

from subprocess import Popen, PIPE, STDOUT
import threading

class Supershell:
    def __init__(self):
        self.lock = threading.Lock()

# Alternative: use a Queue object.
    def put(self, item):
        self.lock.acquire()
        try:
            self.items.append(item)
        finally:
            self.lock.release()


    def get(self):
        if not self.items:
            return None
        self.lock.acquire()
        try:
            res = self.items[0]
            del self.items[0]
            return res
        finally:
            self.lock.release()


    def run(self, cmd):
        """Run a command in a separate thread.
        self.ok is set to None, changing to True or False when the thread
        completes.
        """
        self.items = []
        self.ok = None
        self.pthread = threading.Thread(target=self.start, args=(cmd,))
        self.pthread.start()


    def start(self, cmd):
        """Run a command in a separate process.
        This reads output line by line and passes it on, but it won't
        return until the process has completed, so it should not be called
        from a thread that needs to be reactive.
        """
        self.result = ""
        self.process = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            self.result += line
            # Pass on the output of the process
            self.put(line)

        self.ok = (self.process.returncode == 0)


    def kill(self):
        """Kill the current subprocess.
        As the 'start' method blocks, this can only be called from a
        separate thread.
        """
        if self.process.returncode == None:
            self.process.kill()
