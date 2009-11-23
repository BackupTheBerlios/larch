#!/usr/bin/env python
#
# xkmap.py   --  Simple GUI for 'setxkbmap'
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

import os, tempfile, re, traceback, pwd
from subprocess import call, Popen, PIPE, STDOUT
# For running utilities as root:
if os.getuid() != 0:
    import pexpect



XKMAPMARK1 = '#XKMAP+'
XKMAPMARK2 = '#XKMAP-'


# Get xkmap directory
thisdir = os.path.dirname(os.path.realpath(__file__))
# Get configuration for system-dependent paths, etc.
execfile(thisdir + '/xkmap.conf')

import gettext
t = gettext.translation('xkmap', thisdir + '/i18n', fallback=True)
_ = t.ugettext


STANDARDLAYOUT = ('-', 'Standard')

class Xkmap:
    def __init__(self, ui, chroot=""):
        """The chroot parameter allows the module to work on mounted
        systems, rather than the currently running one.
        """
        self.chroot = chroot
        self.with_ldm = False
        self.ui = ui


    def ldm_available(self):
        return os.path.isfile(self.chroot + detect_ldm)


    def buildgui(self):
        """Build the xkmap main widget.
        """
        self.ui.widget("Frame", "xkmap:frame")
        self.ui.widget("Label", "xkmap:layout_l", text=_("Layout (language)"))
        self.ui.widget("ComboBox", "^xkmap:layout", typewriter=True)
        self.ui.widget("Label", "xkmap:variant_l", text=_("Variant"))
        self.ui.widget("ComboBox", "^xkmap:variant", typewriter=True)
        self.ui.widget("Label", "xkmap:command_l", text=_("Command"))
        self.ui.widget("LineEdit", "xkmap:command", ro=True)
        self.ui.widget("CheckBox", "^xkmap:ldm",
                text=_("Use display manager for global setting (default is HAL)"))

        self.ui.layout("xkmap:frame", ["*GRID*",
                ["*+*", "xkmap:layout_l", "xkmap:layout"],
                ["*+*", "xkmap:variant_l", "xkmap:variant"],
                ["*+*", "xkmap:command_l", "xkmap:command"],
                ["*+*", "xkmap:ldm", "*-"],
            ])
        if self.ldm_available():
            self.ui.addslot("xkmap:ldm*toggled", self.setGlobalLdm)
        else:
            self.ui.command("xkmap:ldm.enable", False)


    def setGlobalLdm(self, on):
        self.with_ldm = on


    def init(self):
        self.password = None
        self.layouts, self.allVariants = self.getLayouts()

        # Get initial layout
        l, self.v0 = self.getHalLayout()
        if self.ldm_available():
            self.ldmfile = XrcFile(self.chroot + xinitrc_ldm, self.rootsave)
            if self.ldmfile.keymap:
                l, self.v0 = self.ldmfile.keymap.split(":")
        if not self.chroot:
            self.xrcfile = XrcFile(pwd.getpwuid(os.getuid())[5] + "/.xinitrc")
            if self.xrcfile.keymap:
                l, self.v0 = self.xrcfile.keymap.split(":")

        self.ui.addslot("xkmap:layout*changed", self.newLayout)
        self.ui.addslot("xkmap:variant*changed", self.newVariant)

        # Populate layouts widget
        li, i = 0, 0
        items = []
        for item in self.layouts:
            items.append("%-16s%s" % item)
            if item[0] == l:
                li = i
            i += 1
        self.ui.command("xkmap:layout.set", items, li)
        self.newLayout(li)


    def setSys(self):
        if self.with_ldm:
            op = self.ldmfile.set(self.layout, self.variant)
            if op:
                op = _("Couldn't set display manager keymap:\n%s") % op
        else:
            op = self.setHalLayout(self.layout, self.variant)
            if (not op) and self.ldm_available() and os.path.isfile(self.chroot + xinitrc_ldm):
                self.ldmfile.set()
        if op:
            self.ui.error(op)
        else:
            self.setNow()


    def setNow(self):
        if not self.chroot:
            call(self.command, shell=True)
        self.v0 = self.variant


    def setUser(self):
        op = self.xrcfile.set(self.layout, self.variant)
        if op:
            self.ui.error(_("Couldn't set user's persistent keymap:\n%s") % op)
        else:
            self.setNow()


    def clearUser(self):
        op = self.xrcfile.set()
        if op:
            self.ui.error(_("Couldn't clear user's persistent keymap:\n%s") % op)


    def newLayout(self, index):
        self.layout = self.layouts[index][0]
        self.variants = self.allVariants.get(self.layout)
        if not self.variants:
            self.variants = [STANDARDLAYOUT]
        vi, i = 0, 0
        items = []
        for item0, item1 in self.variants:
            if len(item1) > 30:
                item1 = item1[:30]
            items.append("%-16s%s" % (item0, item1))
            if item0 == self.v0:
                vi = i
            i += 1
        self.ui.command("xkmap:variant.set", items, vi)
        self.newVariant(vi)


    def newVariant(self, index):
        if index >= 0:
            self.variant = self.variants[index][0]
            self.ui.command("xkmap:variant.x__tt", self.variants[index][1])
            self.showCommand()


    def showCommand(self):
        self.command = "setxkbmap -layout %s" % self.layout
        if self.variant != "-":
            self.command += " -variant " + self.variant
        self.ui.command("xkmap:command.x__text", self.command)


    def getHalLayout(self):
        rx1 = re.compile(r'(\s*<merge.+key="input.xkb.layout".*)>([a-z]+)</merge>(.*)')
        rx2 = re.compile(r'(\s*<merge.+key="input.xkb.variant".*)>([a-z]+)</merge>(.*)')
        rx3 = re.compile(r'(\s*<merge.+key="input.xkb.variant".*)/>(.*)')

        if os.path.isfile(self.chroot + fdipath):
            f = self.chroot + fdipath
        else:
            assert os.path.isfile(self.chroot + fdipath0)
            f = self.chroot + fdipath0
        fh = open(f)
        self.xmlLines = fh.readlines()
        fh.close()

        index = -1
        for line in self.xmlLines:
            index += 1
            m = rx1.match(line)
            if m:
                self.layoutl = list(m.groups())
                self.layout_index = index
                continue
            m = rx2.match(line)
            if m:
                self.variantl = list(m.groups())
                self.variant_index = index
                continue
            m = rx3.match(line)
            if m:
                self.variantl = list(m.groups())
                self.variantl.insert(1, "-")
                self.variantl[0] = self.variantl[0].rstrip()
                self.variant_index = index

        self.layoutl[2] = self.variantl[2].rstrip()
        self.variantl[2] = self.variantl[2].rstrip()
        return (self.layoutl[1], self.variantl[1])


    def setHalLayout(self, layout, variant):
        self.xmlLines[self.layout_index] = ("%s>%s</merge>%s\n" %
                (self.layoutl[0], layout, self.layoutl[2]))

        if variant == "-":
            self.xmlLines[self.variant_index] = ("%s />%s\n" %
                    (self.variantl[0], self.variantl[2]))
        else:
            self.xmlLines[self.variant_index] = ("%s>%s</merge>%s\n" %
                    (self.variantl[0], variant, self.variantl[2]))

        # Need to save file as root
        op = self.rootsave(self.xmlLines, self.chroot + fdipath)
        if op:
            return _("Couldn't save keymap to '%s':/\n%s") % (self.chroot + fdipath, op)
        if not self.chroot:
            op = self.rootrun(halrestart)
            if op:
                self.ui.error(_("Couldn't restart HAL:\n%s") % op)
        return ""


    def getLayouts(self):
        # Read 'base.lst'
        blf = open(self.chroot + base_lst)
        while blf.readline().strip() != "! layout": pass

        layouts = []
        while True:
            line = blf.readline().strip()
            if line:
                if line == "! variant": break
                layouts.append(tuple(line.split(None, 1)))

        layouts.sort()

        allVariants = {}
        while True:
            line = blf.readline().strip()
            if not line: continue
            if line == "! option": break
            parts = line.split(None, 2)
            line = (parts[0], parts[2])
            layout = parts[1].rstrip (":")
            if not allVariants.has_key(layout):
                allVariants[layout] = [STANDARDLAYOUT]
            allVariants[layout].append(line)

        blf.close()
        return (layouts, allVariants)


    def rootsave(self, lines, path):
        """Save the lines to a root owned file at 'path'.
        Return an empty string for ok, else message.
        """
        try:
            if os.getuid() == 0:
                fh = open(path, "w")
                for line in lines:
                    fh.write(line)
                fh.close()
                return ""

            fh, temp_path = tempfile.mkstemp()
            f = os.fdopen(fh, "w")
            for line in lines:
                f.write(line)
            f.close()

            cmd = ("mv '%s' '%s' && chmod 644 '%s' && chown root:root '%s'"
                    % (temp_path, path, path, path))
            op = self.rootrun(cmd)
            if op:
                os.remove(temp_path)
            return op

        except:
            return traceback.fmt_exc()


    def rootrun(self, cmd):
        """Run the given command as 'root'.
        Return "" on successful completion, otherwise an error message.
        """
        if (os.getuid() == 0):
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
            o = p.communicate()[0]
            return "" if p.returncode == 0 else o
        elif not self.password:
            op = self.get_rootpw(cmd)
            if op:
                return op
        return self.asroot(cmd)


    def get_rootpw(self, cmd):
        okpw = self.ui.textLineDialog(_("Please enter root password:"),
                "xkmap: root pw", pw=True)
        if okpw[0]:
            self.password = okpw[1]
            op = self.asroot('true')
            if op:
                self.password = None
                return _("Incorrect root password")
            else:
                return ""
        else:
            return _("You cancelled the operation")


    def asroot(self, cmd):
        """Run a command as root, using the known password.
        """
        child = pexpect.spawn('su -c "%s && echo -n _OK_"' % cmd)
        child.expect(':')
        child.sendline(self.password)
        child.expect(pexpect.EOF)
        o = child.before.strip()
        return ("" if o.endswith('_OK_') else o)



class XrcFile:
    def __init__(self, path, rootsave=None):
        """Read the given file - if it exists - and note the place where
        xkmap tags are (if any).
        Extract the keyboard mapping, if possible.
        """
        self.rootsave = rootsave
        self.path = path
        self.keymap = None
        self.mark1 = -1
        self.mark2 = False

        xkset = re.compile(r"\s*xkmap-set")
        self.xrc = []
        if os.path.isfile(path):
            fh = open(path)
            ln = 0
            for line in fh:
                if line.startswith(XKMAPMARK1):
                    if self.mark1 < 0:
                        self.mark1 = ln

                elif xkset.match(line):
                    parts = line.split()
                    if (len(parts) > 1) and (":" in parts[1]):
                        self.keymap = parts[1]

                elif line.startswith(XKMAPMARK2):
                    if self.mark1 >= 0:
                        self.mark2 = True

                elif (self.mark1 < 0) or self.mark2:
                    ln += 1
                    self.xrc.append(line)
            fh.close()


    def set(self, layout=None, variant="-"):
        if self.mark1 < 0:
            self.mark1 = 0
        xrc = (self.xrc[:self.mark1]
                + [XKMAPMARK1 + "\n",
                    "xkmap-set %s:%s\n" % (layout, variant),
                    XKMAPMARK2 + "\n"]
                + self.xrc[self.mark1:] if layout else self.xrc)
        if self.rootsave:
            return self.rootsave(xrc, self.path)

        else:
            try:
                fh = open(self.path, "w")
                for line in xrc:
                    fh.write(line)
                fh.close()
            except:
                return traceback.fmt_exc()
        return ""

