# backend.py
#
# (c) Copyright 2009 Michael Towers <gradgrind[at]online[dot]de>
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
# 2009.03.25

from subprocess import Popen, PIPE, STDOUT


class Backend:
    """Interaction with the machine is dealt with via the interface provided
    in this class, in general by means of running small shell scripts which
    are in the larchin-syscalls package and can be on a separate machine
    from that on which larchin is running.
    """
    def __init__(self, host=None):
        self.host = host

        self.process = None
        self.interrupt = None
        self.error = None
        self.outputmethod = None

        assert (self.xcall("init") == ""), (
                "Couldn't initialize installation system")


# I am not using this at the moment, I just thought it might be useful.
    def read_output_cb(self, textline):
        """By setting self.outputmethod to a (gui thread) method, the
        output of an xcall command can be processed line-by-line in the gui.
        """
        self.outputmethod(textline)
        return False        # So this method is not repeatedly called


    #************ Methods for calling bash scripts

    def xsendfile(self, path, dest):
        """Copy the given file (path) to dest on the target.
        """
        plog("COPY FILE: %s (host) to %s (target)" % (path, dest))
        if self.host:
            self.process = Popen("scp -q %s root@%s:%s" %
                    (path, self.host, dest), shell=True,
                    stdout=PIPE, stderr=STDOUT)
            plog(self.process.communicate()[0])
            self.process = None
        else:
            shutil.copyfile(path, dest)
        assert self.interrupt == None


    def xcall_local(self, cmd):
        """Call a function on the same machine.
        """
        xcmd = ("%s/syscalls/%s" % (basePath, cmd))
        return Popen(xcmd, shell=True, stdout=PIPE, stderr=STDOUT, bufsize=1)


    def xcall_net(self, cmd, opt=""):
        """Call a function on another machine.
        Public key authentication must be already set up so that no passsword
        is required.
        """
        xcmd = ("ssh %s root@%s /opt/larchin/syscalls/%s" %
                (opt, self.host, cmd))
        return Popen(xcmd, shell=True, stdout=PIPE, stderr=STDOUT, bufsize=1)


    def terminal(self, cmd):
        """Run a command in a terminal. The environment variable 'XTERM' is
        recognized, otherwise one will be chosen from a list.
        """
        term = os.environ.get("XTERM", "")
        if (os.system("which %s &>/dev/null" % term) != 0):
            for term in ("terminal", "konsole", "xterm", "rxvt", "urxvt"):
                if (os.system("which %s &>/dev/null" % term) != 0):
                    term = None
                else:
                    break

        assert term, _("No terminal emulator found")
        if (term == "terminal"):
            term += " -x "
        else:
            term += " -e "

        plog("TERMINAL: %s" % cmd)
        self.process = Popen(term + cmd, shell=True)
        plog(self.process.communicate()[0])
        self.process = None
        assert self.interrupt == None


    def xcall(self, cmd, opt="", log=True):
        if self.host:
            self.process = self.xcall_net(cmd, opt)
        else:
            self.process = self.xcall_local(cmd)
        self.processes.append(process)

        if log:
            plog("XCALL: %s" % cmd)
        op = ""
        self.oplines = []
        while True:
            line = self.process.stdout.readline()
            if not line: break
            # Allow the output from this call to be processed line-by-line
            # by a method running in the gui thread.
            if self.outputmethod:
                mainWindow.idle_call(self.read_output_cb, line)
            self.oplines.append(line)
            op += line
            if log:
                plog(line)
        if log:
            plog("END-XCALL")

        self.process = None
        assert self.interrupt == None
        if op.endswith("^OK^"):
            self.okop = op
            return ""
        else:
            return op

