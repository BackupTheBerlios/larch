#!/usr/bin/env python
#
# installation.py
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
# 2009.06.07

"""This module handles the Arch system which has been or will be installed
to be made into a larch live system. If the installation path is "/" (i.e.
for larchifying the running system) this module will not be used.
"""

import os, filecmp

class Installation:
    def __init__(self):
        # Do a completely inadequate check for a valid installation?
        # (An adequate check is impossible.)


        # Generate pacman.conf, including larch repo - call this whenever
        # pacman.conf is needed.
        #self.make_pacman_conf()

        # Construct the pacman command to use for working with the larch
        # installation - call this whenever pacman is needed.
        #self.make_pacman_command()
        return


    def make_pacman_conf(self, veto=[]):
        """Construct the pacman.conf file used by larch.
        If a list of repository names is passed in 'veto' these will not
        be included in the result.
        This pacman.conf must be regenerated if anything concerning the
        repositories changes. It might be easier to regenerate every time
        it is used.
        The return value is a list of the names of the repositories which
        are included.

        *** A template for pacman.conf ***

        To make it easier to edit the relevant bits of pacman.conf
        automatically a special template form is used. There is a default
        form supplied with larch (data/pacman.conf.0), which should be
        updated if the default pacman.conf in the pacman package gets
        changed. A customized version can be supplied in the profile
        (also under the name pacman.conf.0). When larch needs to use
        'pacman -S' this template will be filled out with the available
        information to produce the pacman.conf which is then used.

        Basically the same version of this file will be used in the
        installed system, unless the profile provides an etc/pacman.conf
        file in the overlay.
        """
        # The 'DBPath' cannot be easily changed when the -r option to
        # pacman is used, because the given value is then treated as an
        # absolute path.
        self.pacmandbdir = "var/lib/pacman/sync"
        repos = []
        pc0 = os.path.join(config.profile, "pacman.conf.0")
        if not os.path.isfile():
            pc0 = os.path.join(base_dir, "data/pacman.conf.0"))

        fhi = open(pc0)
        fho = open(os.path.join(config.working_dir, "pacman.conf"), "w")
        skipping = False
        for line in fhi:
            if line.startswith("#***"):
                continue
            if skipping:
                if line.strip():
                    skipping = False
                    fho.write("\n")
                continue
            if line.startswith("*** "):
                repo = line.split[1]
                if repo in veto:
                    skipping = True
                    continue
                repos.append(repo)
                fho.write("[%s]\n" % repo)
                if repo == "larch":
                    url = config.get("larch_url") + config.get("platform")
                    fho.write("Server = %s\n" % url)
                else:
                    # Do I want to support multiple mirrors?
                    # I could return a list, or simply a multiline string.
                    # Of course the code here would need to be changed
                    # accordingly.
                    url = config.get("mirror").replace("$repo", repo)
                    if url:
                        fho.write("Server = %s%s\n" % (url,
                                config.get("platform"))
                    # If no mirror is set the mirrorlist from the host
                    # will be used (/etc/pacman.d/mirrorlist), as long as
                    # pacman.conf has appropriate entries (by default
                    # this should be the case).
            else:
                fho.write(line)
                if line.startswith("["):
                    repo = line.strip().strip("[]")
                    if repo != "options":
                        repos.append(repo)

        fhi.close()
        fho.close()
        return repos


    def make_pacman_command(self):
        """Construct pacman command. This must be regenerated if the
        working directory, the installation path or the cache directory
        changes. It might be easier to regenerate every time pacman is used.
        """
        self.pacman_cmd = ("%s -r %s --config %s --noconfirm --noprogressbar" %
                (config.pacman, config.get("installation_path"),
                 os.path.join(config.get("working_dir"), "pacman.conf")))
        cache = config.get("pacman_cache")
        if cache:
            self.pacman_cmd += " --cachedir %s" % cache


    def update_db(self):
        """This updates or creates the pacman-db in the installation.
        Some or all of the repository-dbs may be copied from existing
        versions, the rest are fetched using 'pacman -Sy' together with
        an appropriate pacman.conf file.
        """
        copydbs = config.get("copy-db-list").split()
        repos = self.make_pacman_conf(copydbs)
        syncdir = os.path.join(config.get("install_path", self.pacmandbdir)
        supershell("mkdir -p %s" % syncdir)
        for r in copydbs:
            sdir = os.path.join(config.get("pacman_sync"), r)
            ddir = os.path.join(syncdir, r)
            stag = os.path.isfile(os.path.join(sdir, ".lastupdate"))
            dtag = os.path.isfile(os.path.join(ddir, ".lastupdate"))
            if (    os.path.isfile(stag) and os.path.isfile(dtag) and
                    filecmp.cmp(stag, dtag)):
                continue
            if not os.path.isdir(sdir):
                config_error(_("Cannot copy database for '%s' repository:\n"
                        "  Directory %s doesn't exist.") % (r, sdir))
                return False
            supershell("rm -rf %s" % ddir)
            if not supershell("cp -a %s %s" % (sdir, syncdir)).ok:
                run_error(_("Copying database for '%s' repository failed")
                        % os.path.basename(sdir))
                return False

        if repos:
            self.make_pacman_command()
            if not supershell("%s -Sy" % self.pacman_cmd).ok:
                run_error(_("Couldn't synchronize pacman database (pacman -Sy)"))
                return False
        return True


    def install(self):
        """Clear the chosen installation directory and install the base
        set of packages, together with any additional ones listed in the
        file 'addedpacks' (in the profile).
        """

        installation_path = config.get("installation_path")

        if os.path.isdir(installation_path):
            supershell("rm -rf %s/{*,.*}" % installation_path)

        # Ensure installation directory exists and check that device nodes
        # can be created (creating /dev/null is also a workaround for an
        # Arch bug - which may have been fixed, but this does no harm)
        if not (supershell("mkdir -p %s/dev" % installation_path).ok and
                supershell("mknod -m 666 %s/dev/null c 1 3" %
                        installation_path).ok):
            config_error(_("Couldn't write to the installation path (%s).") %
                    installation_path)
            return False
        if not supershell("echo 'test' >%s/dev/null" % installation_path).ok:
            config_error(_("The installation path (%s) is mounted 'nodev'.") %
                    installation_path)
            return False

        # I should also check that it is possible to run stuff in the
        # installation directory.
        supershell("cp $( which echo ) %s" % installation_path)
        if not supershell("%s/echo 'yes'" % installation_path).ok:
            config_error(_("The installation path (%s) is mounted 'noexec'.") %
                    installation_path)
            return False
        supershell("rm %s/echo" % installation_path)

        # Fetch package database
        if not self.update_db():
            return False

        # Get list of packages in 'base' group, removing those in the
        # list of vetoed packages.
        veto_packages = []
        veto_file = os.path.join(config.get("profile_dir"), "baseveto")
        if os.isfile(veto_file):
            fh = open(veto_file)
            for line in fh:
                line = line.strip()
                if line and (not line.startswith("#")):
                    veto_packages.append(line)
            fh.close()
        packages = []
        self.make_pacman_command()
        # In the next line the call could be done as a normal user.
        for line in supershell("%s -Sg base" % self.pacman_cmd).result:
            l = line.split()
            if l and (l[0] == "base") and (l[1] not in veto_packages):
                packages.append(l[1])

        # Add necessary packages
        for p in ["larch-live", "squashfs-tools", "lzop"]:
            if p not in packages:
                packages.append(p)

        # Add additional packages and groups, from 'addedpacks' file.
        addedpacks_file = os.path.join(config.profile, "addedpacks")
        fh = open(addedpacks_file)
        for line in fh:
            line = line.strip()
            if (line and (not line.startswith("#"))
                    and (line not in packages)):
                packages.append(line)
        fh.close()

        # Do I want to be able to install custom packages with pacman -U?
        # It shouldn't be difficult, but it would probably be better to
        # make a local custom repository and include that in 'addedpacks'.

        # Now do the actual installation.
        ok = self.pacmancall("-S", " ".join(packages)))
        if not ok:
            run_error(_("Package installation failed"))
        return ok


    def pacmancall(self, op, arg):
        # (a) Prepare the destination directory
        supershell("mkdir -p %s/{sys,proc} &&"
                " mount --bind /sys %s/sys && mount --bind /proc %s/proc"
                % ((config.install_path,)*3))

        # (b) Call pacman
        # Note that I will probably want incremental output from this.
        ok = supershell("%s %s %s" % (self.pacman_cmd, op, arg)).ok

        # (c) Remove bound mounts
        supershell("umount %s/proc && umount %s/sys"
                % ((config.install_path,)*2))

        return ok



if __name__ == "__main__":
    pass


