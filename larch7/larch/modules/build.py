#!/usr/bin/env python
#
# build.py
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
# 2009.08.28

import os, sys
from glob import glob
from subprocess import Popen, PIPE, STDOUT


class Builder:
    """This class manages 'larchifying' an Arch Linux installation.
    """
    def __init__(self):
        pass

    def oldsqf_available(self):
        self.installation_dir = config.ipath()
        # Define the working area - it must be inside the installation
        # because of the use of chroot for some functions
        self.larch_dir = config.ipath(config.larch_build_dir)
        # Location for the live medium image
        self.medium = config.ipath(config.medium_dir)

        self.system_sqf = config.ipath(config.system_sqf)
        if os.path.isfile(self.medium + "/larch/system.sqf"):
            return True
        else:
            return os.path.isfile(self.system_sqf)


    def ssh_available(self):
        return os.path.isfile(config.ipath("usr/bin/ssh-keygen"))


    def build(self, sshgen, useoldsqf):
        self.installation0 = self.installation_dir if self.installation_dir != "/" else ""
        if not (self.installation0 or command.uiask("confirmDialog", _(
                    "Building a larch live medium from the running system is\n"
                    "an error prone process. Changes to the running system\n"
                    "made while running this function may be only partially\n"
                    "incorporated into the compressed system images.\n\n"
                    "Do you wish to continue?"))):
                return False

        self.profile = config.get("profile")
        self.overlay = config.ipath(config.overlay_build_dir)
        command.log("#Initializing larchify process")

        if useoldsqf:
            if os.path.isfile(self.medium + "/larch/system.sqf"):
                supershell("mv %s/larch/system.sqf %s" %
                        (self.medium, self.larch_dir))
        else:
            supershell("rm -f %s" % self.system_sqf)

        # Clean out temporary area and create overlay directory
        supershell("rm -rf %s/tmp && mkdir -p %s" %
                (self.larch_dir, self.overlay))

        if not self.find_kernel():
            return False

        if not self.system_check():
            return False

        command.log("#Beginning to build larch medium files")
        # Clear out the directory
        supershell("rm -rf %s && mkdir -p %s/{boot,larch}" %
                (self.medium, self.medium))

        # kernel
        supershell("cp -f %s/boot/%s %s/boot/larch.kernel" %
                (self.installation0, self.kname, self.medium))
        # Remember file name (to ease update handling)
        supershell('echo "%s" > %s/larch/kernelname'
                % (self.kname, self.medium))

        # if no saved system.sqf, squash the Arch installation at self.installation_dir
        if not os.path.isfile(self.system_sqf):
            command.log("#Generating system.sqf")
            # root directories which are not included in the squashed system.sqf
            ignoredirs = "boot dev mnt media proc sys tmp .livesys "
            ignoredirs += config.larch_build_dir.lstrip("/")
            # /var stuff
            ignoredirs += " var/log var/tmp var/lock var/cache/pacman/pkg"
            # others
            ignoredirs += " usr/lib/locale"

            if not command.chroot('/sbin/mksquashfs "/" "%s" -e %s'
                    % (config.system_sqf, ignoredirs)):
                command.error("Warning", _("Squashing system.sqf failed"))
                return False
            # remove execute attrib
            supershell("chmod oga-x %s" % self.system_sqf)

        # move system.sqf to medium directory
        supershell("mv %s %s/larch" % (self.system_sqf, self.medium))

        # prepare overlay
        command.log("#Generating larch overlay")
        # Copy over the overlay from the selected profile
        if os.path.isdir("%s/rootoverlay" % self.profile):
            supershell("cp -rf %s/rootoverlay/* %s" % (self.profile, self.overlay))

###+ This code can be changed or omitted when the rc. script hooks have
###  established themselves firmly.
        # Prepare inittab
        inittab = self.overlay + "/etc/inittab"
        itsave = inittab + ".larchsave"
        it0 = self.installation0 + "/etc/inittab"
        if (not os.path.isfile(it0 + ".larchsave")) and (not os.path.isfile(itsave)):
            # Save the original, if there isn't already a saved one
            supershell("cp %s %s" % (it0, itsave))
        if not os.path.isfile(inittab):
            supershell("cp %s/etc/inittab %s/etc" % (it0, inittab))
        supershell('sed -i "s|/etc/rc.sysinit|/etc/rc.larch.sysinit|" %s' % inittab)
        supershell('sed -i "s|/etc/rc.shutdown|/etc/rc.larch.shutdown|" %s' % inittab)
###-

        command.log("#Generating larch initcpio")
        command.script("larch-initcpio '%s' '%s' '%s'" %
                (self.installation0, self.overlay, self.ufs))
        # Move initcpio to medium directory
        supershell("mv %s/boot/larchnew.img %s/boot/larch.img" %
                (self.installation0, self.medium))

        command.log("#Generating glibc locales")
        command.script("larch-locales '%s' '%s'" % (self.installation0,
                self.overlay))

        if sshgen:
            # ssh initialisation - done here so that it doesn't need to
            # be done when the live system boots
            command.log("#Generating ssh keys to overlay")
            sshdir = config.overlay_build_dir + "/etc/ssh"
            supershell("mkdir -p %s" % config.ipath(sshdir))
            for k, f in [("rsa1", "ssh_host_key"), ("rsa", "ssh_host_rsa_key"),
                    ("dsa", "ssh_host_dsa_key")]:
                command.chroot('ssh-keygen -t %s -N "" -f %s/%s >/dev/null'
                        % (k, sshdir, f), ["dev"])

        # Ensure the hostname is in /etc/hosts
        command.script("larch-hosts %s %s" % (self.installation0, self.overlay))

        # Handle /mnt
        supershell("mkdir -p %s/mnt" % self.overlay)
        for d in os.listdir("%s/mnt" % self.installation0):
            if os.path.isdir("%s/mnt/%s" % (self.installation0, d)):
                supershell("mkdir %s/mnt/%s" % (self.overlay, d))

        # Ensure there is a /boot directory
        supershell("mkdir -p %s/boot" % self.overlay)

        command.log("#Squashing mods.sqf")
        if not command.chroot('/sbin/mksquashfs "%s" "%s/larch/mods.sqf"'
                % (config.overlay_build_dir, config.medium_dir)):
            command.error("Warning", _("Squashing mods.sqf failed"))
            return False
        # remove execute attrib
        supershell("chmod oga-x %s/larch/mods.sqf" % self.medium)

        supershell("rm -rf %s" % self.overlay)
        # The medium boot directory needs to be kept outside of the medium
        # directory to allow multiple, different media to be built easily.
        supershell("mv %s/boot %s/tmp" % (self.medium, self.larch_dir))


    def system_check(self):
        command.log("#Testing for necessary packages and kernel modules")
        fail = ""
        warn = ""

        mdep = config.ipath("lib/modules/%s/modules.dep" % self.kversion)
        if Popen(["grep", "/squashfs.ko", mdep], stdout=PIPE, stderr=STDOUT).wait() != 0:
            fail += _("No squashfs module found\n")

        if Popen(["grep", "/aufs.ko", mdep], stdout=PIPE, stderr=STDOUT).wait() == 0:
            self.ufs='_aufs'

        elif Popen(["grep", "/unionfs.ko", mdep], stdout=PIPE, stderr=STDOUT).wait() == 0:
            self.ufs='_unionfs'

        else:
            fail += _("No aufs or unionfs module found\n")

        for p in ["larch-live", "squashfs-tools", "aufs2-util", "lzop"]:
            if not self.haspack(p):
                fail += _("Package '%s' is needed by larch systems\n") % p

        if not self.haspack("syslinux"):
            warn += _("Without package 'syslinux' you will not be able\n"
                    "to create syslinux or isolinux booting media\n")

        if (not self.haspack("cdrkit")) and (not self.haspack("cdrtools")):
            warn += _("Without package 'cdrkit' (or 'cdrtools') you will\n"
                    "not be able to create CD/DVD media\n")

        if not self.haspack("eject"):
            warn += _("Without package 'eject' you will have problems\n"
                    "using CD/DVD media\n")

        if warn:
            cont = command.uiask("confirmDialog", _("WARNING:\n%s"
                    "\n    Continue building?") % warn)
        else:
            cont = True

        if fail:
            command.uiask("infoDialog", _("ERROR:\n%s") % fail)
            return False

        return cont


    def haspack(self, package):
        """Check whether the given package is installed.
        """
        for p in os.listdir(config.ipath("var/lib/pacman/local")):
            if p.rsplit("-", 2)[0] == package:
                return True
        return False


    def find_kernel(self):
        # The uncomfortable length of this function is deceptive,
        # most of it is for dealing with errors.
        command.log("#Seeking kernel information")
        script = "%s/kernel" % self.profile
        if os.path.isfile(script):
            p = Popen([script], stdout=PIPE, stderr=STDOUT)
            r = p.communicate()[0]
            if p.returncode == 0:
                self.kname, self.kversion = r.split()

            else:
                fatal_error(_("Problem running %s:\n  %s") % (script, r))
                return False
        else:
            kernels = glob(config.ipath("boot/vmlinuz*"))
            if len(kernels) > 1:
                fatal_error(_("More than one kernel found:\n  %s") %
                        "\n  ".join(kernels))
                return False
            elif not kernels:
                fatal_error(_("No kernel found"))
                return False
            self.kname = os.path.basename(kernels[0])

            self.kversion = None
            for kv in os.listdir(config.ipath("lib/modules")):
                if os.path.islink(config.ipath("lib/modules/%s/build" % kv)):
                    if self.kversion:
                        fatal_error(_("More than one set of kernel modules in %s")
                                % config.ipath("lib/modules"))
                        return False
                    self.kversion = kv
                else:
                    kmpath = config.ipath("lib/modules/%s" % kv)
                    command.log("#Unexpected kernel files at %s" % kmpath)
                    # Try to find packages concerned
                    p = Popen(["find", ".", "-name", "*.ko"], cwd=kmpath,
                            stdout=PIPE, stderr=STDOUT)
                    r = p.communicate()[0]
                    if p.returncode == 0:
                        packs = []
                        for km in r.split():
                            a = command.chroot("pacman -Qoq /lib/modules/%s/%s"
                                    % (kv, km))

                            if a:
                                pack = "-".join(a[0].split())
                                if pack not in packs:
                                    packs.append(pack)
                                    command.log("# Package: %s" % pack)

                    else:
                        command.log("#Couldn't determine guilty packages")

                    if not command.uiask("confirmDialog", _("WARNING:\n"
                            "  You seem to have installed a package containing modules\n"
                            "which aren't compatible with your kernel (see log).\n"
                            "Please check that this won't cause problems.\n"
                            "Maybe you need the corresponding package for your kernel?\n"
                            "\n    Continue building?")):
                        return False

        if not self.kversion:
            fatal_error(_("Couldn't find kernel modules"))
            return False

        command.log("#Kernel: %s   -   version: %s" % (self.kname, self.kversion))
        command.chroot("depmod %s" % self.kversion)
        return True
