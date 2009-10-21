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
# 2009.10.21

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
  <li>Generate /etc/fstab.</li>
  <li>Unmount installation partitions.</li>
</ol>
</p>

<h3>Device recognition via LABEL or UUID</h3>
<p>Because of the way block devices are detected in <em>Linux</em> it is
possible under certain circumstances for a partition to get assigned a
different name (e.g. /dev/sda can become /dev/sdb) from one boot to the
next. For this reason it is often sensible to address these devices in a
more stable way in grub and /etc/fstab.
</p>
<p>The default in <em>larchin</em> is to use the device LABEL, if there
is one, otherwise the UUID. Only if the checkbox 'Use device name' is
checked will the device name (/dev/sda1, etc.) be used.
</p>

<h3>Customizing Formatting</h3>
<p>To allow tweaking of the way partitions are formatted, the syscall
script 'part-format' sources a script in the sub-directory 'tweaks' with
    a name built from the file-system type, 'tweaks/format-<em>fstype</em>'.
    If you want to make use of this feature, see the 'part-format' script.
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
        ui.newwidget("CheckBox", "^install:devname",
                tt=_("Use device name (/dev/sda1, etc.), not LABEL or UUID,"
                        " in /etc/fstab and for grub"),
                text=_("Use /dev/sda1, etc. (NOT LABEL / UUID)"))

        ui.layout("page:install", ["*VBOX*", "install:l1", "install:devname"])

    def setup(self):
        return


    def select_page(self, init, partitions=[]):
        self.initialize = init
        if init:
            self.partlist = partitions
#debugging
            if "P" in dbg_flags:
                self.partlist = [
                        ["/", "/dev/sda1", "ext4"],
                        ["swap", "/dev/sda2", ""],
                        ["/home", "/dev/sda5", "ext4"]]
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
#debugging
        if "f" not in dbg_flags:
#-
            if not installer.format():
                installer.tidy()
                return

        # Mount
        if not installer.mount():
            installer.tidy()
            return

        # Copy system
#debugging
        if "i" not in dbg_flags:
#-
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

            # initramfs
            ui.progressPopup.add(_("Generating initramfs"))
            if not backend.initramfs():
                installer.tidy()
                return

        # /etc/fstab (last step here, so don't need check)
        ui.progressPopup.add(_("Generating /etc/fstab"))
        ok = self.fstab(self.partlist)

        # Unmount, clear popup
        installer.tidy()
        if ok:
            command.runsignal("&passwd!", self.partlist)


    def fstab(self, partlist, devname=False):
        """Build a suitable /etc/fstab for the newly installed system.
        partlist (entries: [mount-point, device, format-type]) contains
        the partitions which are of main interest to this method.
        """
        # Get a dict of all 'mountable' partitions
        uparts = backend.usableparts()
        # Each entry has the form:
        #    device: (fstype, label, uuid, removable)
        # Check that all fs-types correspond to the desired ones and
        # build lists of automount, noautomount and swap partitions.
        automounts = []
        noautomounts = []
        swaps = []
        for mp, dev, fmt in partlist:
            partinfo = uparts.get(dev)
            label, uuid = partinfo[1:3]
            if not partinfo:
                run_error(_("Unusable partition: %s") % dev)
                return False
            fst = partinfo[0]
            if mp == "swap":
                if fst != "swap":
                    run_error(_("Invalid swap partition: %s") % dev)
                    return False
                swaps.append(("swap", dev, "swap", label, uuid))
            else:
                if fst == "swap":
                    run_error(_("Illegal swap partition: %s") % dev)
                    return False
                if fmt and (fmt != fst):
                    run_error(_("Detected fstype not same as format spec: %s")
                            % dev)
                    return False
                automounts.append((mp, dev, fst, label, uuid))
            del(uparts[dev])
        # Now the partitions not specified in partlist
        for dev, tup in uparts.items():
            if not tup[3]:
                # Only make entries for non-removable devices
                noautomounts.append((None, dev) + tup[0:3])

        fstab = ("# fstab generated by larchin\n"
                "#<file system>   <dir>       <type>      <options>"
                        "    <dump> <pass>\n\n")
        # Unless device names are explicitly selected (devname=True),
        # partition labels will be used, if present, or else UUID.
        automounts.sort()
        for part in automounts:
            pas = '1'if (part[0] == '/') else '2'
            fstab += self.fstabentry(part, devname, pas)

        fstab += ("\nnone            /dev/pts    devpts      defaults"
                        "        0     0\n"
                "none            /dev/shm    tmpfs       defaults"
                        "        0     0\n\n")

        fstab += "# Swaps\n"
        for part in swaps:
            fstab += self.fstabentry(part, devname, 0)

        fstab += "\n# Other partitions\n"
        noautomounts.sort()
        for part in noautomounts:
            fstab += self.fstabentry(part, devname, 0)

        fw = open("/tmp/larchin_fstab", "w")
        fw.write(fstab)
        fw.close()
        backend.xsendfile("/tmp/larchin_fstab", "/etc/fstab")


    def fstabentry(self, part, devname, pas):
        mp = part[0]
        fst = part[2]
        if devname:
            dn = part[1]
        else:
            l = part[3]
            dn = ("LABEL=" + l if l else "UUID=" + part[4])
            opt = "defaults"
            if not mp:
                opt = "users,noauto"
                mp = "/mnt/" + dn.rsplit("/", 1)[1]
                backend.mkdir(mp)

            if fst == "ntfs":
                dn = "#" + dn
                fst = "ntfs-3g"
                opt += ",umask=111,dmask=000"

            elif fst == "vfat":
                dn = "#" + dn
                opt += ",umask=111,dmask=000"

            elif fst != "swap":
                opt += ",noatime"

            return ("%-15s %-12s %-8s %s  0  %s\n"
                    % (dn, mp, fst, opt, pas))



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

