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
# 2009.10.15

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
<p>TODO: describe them
</p>
<h3>Mount flags</h3>
<p>TODO: describe them
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
<p>%s</p>""")


class Stage:
    def getHelp(self):
        return doc

    def connect(self):
        return [
                ("&install&", self.select_page),
                ("&do-install&", self.do_install),
            ]

    def select_page(self, partitions):
        self.partlist = partitions
        command.pageswitch(self.page_index,
                _("Disk formatting and system installation"))

    def __init__(self, index):
        self.page_index = index
        ui.newwidget("HtmlView", "install:l1")

        ui.layout("page:install", ["*VBOX*", "install:l1"])


    def setup(self):
        return


    def init(self):
        """The information passed in self.partlist for each partition is:
        [mount-point, device, size(GB), format, format-flags, mount-flags]
        """
        table = ui.formattable(["Mount-point", "Device", "Size (GB)",
                "Format", "Format-flags", "Mount-flags"], self.partlist)
        ui.command("install:l1.x__html", text % table)


    def ok(self):
        command.runsignal("&do-install&")


    def do_install(self):
        ui.progressPopup.start()
        # Format
        for part in self.partlist:
            dev = part[1]
            fmt = part[3]
            flags = part[4]
            if fmt:
                ui.progressPopup.add(_("Formatting %s") % dev)
                if not backend.format(dev, fmt, flags):
                    self.tidy()
                    return


        # Mount
        self.partlist.sort()    # in case of mounts within mounts
        for part in self.partlist:
            mp = part[0]
            if mp.startswith("/"):
                ui.progressPopup.add(_("Mounting %s to %s") % (part[1], mp))
                if not backend.imount(part[1], mp):
                    self.tidy()
                    return


        # Copy system


        # Delivify

        # larch0

        # initramfs

        # Unmount
        self.tidy()


    def tidy(self):
        ui.progressPopup.end()
        if not backend.unmount():
            fatal_error(_("Can't recover from failed unmounting"))
