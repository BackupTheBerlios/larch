# install.py - format partitions and install system
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
# 2009.10.18

from backend import PartInfo

doc = _("""
<h2>System Installation</h2>
<p>If you press OK now the chosen partitions will be formatted and mounted
and then the <em>live</em> system will be copied onto them.
After this has completed, all the <em>live</em> modifications are
removed/undone so that a normal <em>Arch Linux</em> system is left.
</p>
<p><em>larch(in)</em> also provides for further tweaks during the installation
process by means of the larch/copy/larch0 file on the <em>live</em> medium,
which is run at the end of this stage. The contents of this file are
entirely left up to the creator of the <em>larch</em> profile.
</p>
<p>The individual steps are:
<ol>
  <li>Format installation partitions.</li>
  <li>Mount installation partitions.</li>
  <li>Copy system to installation partitions.</li>
  <li>Remove <em>live</em>-specific features.</li>
  <li>Perform custom installation tweaks (medium:larch/copy/larch0).</li>
  <li>Generate new initramfs.</li>
  <li>Unmount installation partitions.</li>
</ol>
</p>
<h3>Format flags</h3>
<p>TODO: describe them. Can these be done later? What about a tweaks
page (e.g. for fsck intervals), or should all this stuff be left to
separate utilities, as they are not specific to installation?
The existing tweaks can be dnoe later, though for dir_index it may be
useful to run 'e2fsck -D'.
</p>
<h3>Mount flags</h3>
<p>TODO: describe them - or, rather, shouldn't mount option come later,
when /etc/fstab is being built?!
</p>""")

text = _("""
<p>The <em>live</em> system will be installed to the selected partition(s)
and all <em>live</em>-specific alterations will be undone so that a normal
<em>Arch Linux</em> installation results.
</p>
<p>Please check that the formatting of the following partitions and their
use within the new installation (mount-points) corresponds with what you
had in mind. Accidents could well result in serious data loss.
</p>
<p align="center">%s</p>""")


class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&install!", self.select_page),
                ("&do-install&", self.do_install),
            ]

    def __init__(self, index):
        self.page_index = index
        ui.newwidget("HtmlView", "install:l1")

        ui.layout("page:install", ["*VBOX*", "install:l1"])

    def setup(self):
        return


    def select_page(self, init, partitions=[]):
        self.initialize = init
        if init:
            self.partlist = partitions
#debugging
            if "P" in dbg_flags:
                self.partlist = [
                        ["/", "/dev/sdb1", "ext4"],
                        ["swap", "/dev/sdb2", ""],
                        ["/home", "/dev/sdb5", "ext4"]]
#-
        command.pageswitch(self.page_index,
                _("Disk formatting and system installation"))


    def init(self):
        """The information passed in self.partlist for each partition is:
        [mount-point, device, format-fstype]
        """
        ok = True
        rows = []
        for r in self.partlist:
            pinfo = PartInfo(r[1])
            s = "%6.1f" % pinfo.sizeGB()
            if r[2] == "":
                f = "-"
                fst = pinfo.getfstype()
                if not fst:
                    config_error(_("No fs-type for unformatted partition %s")
                            % r[1])
                    ok = False
            else:
                f = "+"
                fst = r[2]
            rows.append((r[0], r[1], s, f, fst))
        if not ok: return False

        table = ui.formattable(["Mount-point", "Device", "Size (GB)",
                "Format", "fs-type"], rows)
        ui.command("install:l1.x__html", text % table)


    def ok(self):
        command.runsignal("&do-install&")


    def do_install(self):
        ui.progressPopup.start()
        installer = Installer(self.partlist)

        # Format
        if not installer.format():
            installer.tidy()
            return

        # Mount
        if not installer.mount():
            installer.tidy()
            return

        # Copy system
        ui.progressPopup.show_extra(_("Installed MB:"))
        if not installer.copysystem():
            installer.tidy()
            return
        installer.copydone()
        ui.progressPopup.start_percent()

        # Delivify (including running 'larch0' script)
        ui.progressPopup.add(_("Removing live-system modifications"))
        if not backend.delivify():
            installer.tidy()
            return

        # initramfs (last step here, so don't need check)
        ui.progressPopup.add(_("Generating initramfs"))
        ok = backend.initramfs()

        # Unmount, clear popup
        installer.tidy()
        if ok:
            command.runsignal("&fstab!", self.partlist)



class Installer:
    """This class manages the copying of the live system to the disk.
    """
    def __init__(self, partlist):
        self.partlist = partlist
        self.partlist.sort()    # in case of mounts within mounts

    def format(self):
        for part in self.partlist:
            dev = part[1]
            fmt = part[2]
#debugging
            if "f" in dbg_flags: fmt = None
#-
            if fmt:
                ui.progressPopup.add(_("Formatting %s") % dev)
                if not backend.format(dev, fmt):
                    return False
        return True

    def mount(self):
        if self.partlist[0][0] != "/":
            config_error(_("No root partition ('/') found"))
            return False
        mlist = []
        for part in self.partlist:
            mp, dev = part[0], part[1]
            if mp.startswith("/"):
                ui.progressPopup.add(_("Mounting %s at %s") % (dev, mp))
                mlist.append((dev, mp))
        return backend.imounts(mlist)

    def copysystem(self):
        ui.progressPopup.add(_("Copying system to selected partitions"))
        self.rootdir = ""
        self.installed = 0      # bytes
        self.target = 10**7     # bytes
        return backend.copy_system(self.progress)

    def progress(self, line):
        if "!" not in line:
            #debug(line)
            return
        fname, size = line.split("!")
        frdir = fname.lstrip("/").split("/", 1)[0]
        if frdir != self.rootdir:
            self.rootdir = frdir
            ui.progressPopup.add(" ... /%s ..." % frdir)
        self.installed += int(size)
        if self.installed >= self.target:
            self.target = self.installed + 10**6
            mb = (self.installed + 5*10**5) / 10**6
            ui.progressPopup.set_info("%5d" % mb)
            total = backend.gettotalMB()
            ui.progressPopup.set_percent(mb, total if total>0 else 0)

    def copydone(self):
        ui.progressPopup.hide_extra()
        ui.progressPopup.add("Copy finished: %6.1f GB" %
                (float(self.installed) / 10**9))

    def tidy(self):
        ui.progressPopup.end()
        if not backend.unmount():
            fatal_error(_("Can't recover from failed unmounting"))

