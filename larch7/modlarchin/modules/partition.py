#!/usr/bin/env python
#
# partition.py - add and delete partitions
#
# (c) Copyright 2010 Michael Towers (larch42 at googlemail dot com)
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
# 2010.02.22

import backend

"""The question here is how to make this useful but simple ...
I suppose first and foremost it should isolate the installer a bit from some
of the messy details of the low level partition handling, provide a bit of an
abstraction. The extent to which this is possible is, however, limited by the
nature of the devices and partitions themselves.
Use of lvm might allow more flexibility, but at the cost of complexity, so I
tend not to favour this approach.
Certainly it should be possible to install to a selection of already existing
partitions without lvm (the installer already handles this!).
It should also be possible to specify that existing partitions be deleted, to
allow a new partitioning arrangement.
I could limit new partitions to sequential allocation, and also make this
conditional upon the existing partitions allowing this in a 'clean' way.
I could present info about allocation possibilities which deletion of existing
partitions would enable.

Consider:
* Any partition may be marked for inclusion in the installation, possibly
displaying a warning if doesn't meet the normal criteria.
* Partitions may only be created in the free area at the end of the disk,
and then only if that doesn't call for out-of-order partition numbers
(partition n+1 should directly follow partition n on the disk)
* Only partitions which enable or increase the availability of partitionable
space (according to the previous point) may be deleted.

That sounds pretty restrictive, but this tool should aid inexperienced users
and handle commonly occurring situations, especially if I add the possibility
of shrinking the last NTFS partition. Other partitioning requirements could be
met by using another tool, e.g. cfdisk or gparted.

It should be possible to defer the actual repartitioning, so that all
operations (at least on one disk - and maybe this tool will only handle a
single disk installation) can be carried out in one fell swoop, after a
confirmation. If that includes NTFS-shrinking, it would be necessary to
know in advance how much of a shrinkage is possible.

Allocation of mount-points can be done at this stage, or deferred until
later(?) - would only new partitions be given mount-points, or can
existing ones be included? Actually allocation of mount-points is a
separate activity, and so should be handled by a separate stage, especially
when one considers the possibility of the partitioning being skipped
entirely (when using existing partitions). For simple cases, however, it
would be more straightforward to allocate the mount-points at the same
time as the partitions are specified (so that you don't have to
remember what you created each partition for, and then enter them again
when selecting the mount-points). Perhaps a mixture would be possible,
so that formats and mount-points entered during partitioning are simply
carried on to the mount-point selection. This might manifest itself as
a message like: "The following partitions have been selected for the
installation. Press <OK> to start the installation, or <Edit>
to make changes."

(A further option might be to create a logical volume group out of some
or all of the available free space on the disk, but I'm not sure if this
is really a good idea ...)
"""

class Partition:


if __name__ == "__main__":
    import console
    backend.start_translator()

    from optparse import OptionParser, OptionGroup
    parser = OptionParser(usage=_("usage: %prog [options]"))

# The rest hasn't been done yet. The code below is just a copy from grub.py

"""

    parser.add_option("-m", "--mbr", action="store_true", dest="mbr",
            default=False,
            help=_("Install GRUB to Master Boot Record of installation device"))
    parser.add_option("-x", "--exclude", action="store_false", dest="include",
            default=True, help=_("Exclude entries for other bootloaders"))
    parser.add_option("-n", "--noinstall", action="store_true", dest="noinstall",
            default=False, help=_("Don't install GRUB, just print boot entries"))
    parser.add_option("-b", "--listboot", action="store_true", dest="list",
            default=False, help=_("List other, discovered bootloaders"))
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
            default=False, help=_("Suppress output messages, except errors"))
    group = OptionGroup(parser, _("Passing installation partitions"),
            _("   mount-point:device:format:uuid/label ..."
            " More than one such descriptor can be passed, using ',' as"
            " separator.   The first entry should be for root"
            " (mount-point is '/'), swap partitions have mount-point 'swap'."
            "   format should be 'ext4' or 'jfs', for example. If it is"
            " empty, no formatting will be performed. Also swap"
            " partitions should have this field empty.   The final entry"
            " may be empty (implying the system default will be used),"
            " otherwise:   "
            "   -: using straight device names (/dev/sdXN),"
            "   LABEL=xxxxx: using partition labels,"
            "   UUID=xxxxx: using UUIDs"))
    group.add_option("-l", "--partitions", action="store", type="string",
            default="", dest="parts", help=_("Pass partition list"),
            metavar="PARTLIST")
    parser.add_option_group(group)
    (options, args) = parser.parse_args()

    backend.init(console.Console(options.quiet))

    grub = Grub()
    if not grub.init(options.parts.split(',')):
        sys_quit(1)

    if options.list:
        io.out(_("Partitions containing bootloader configuration files:"))
        for dp in grub.get_existing():
            io.out("    %s: %s" % dp, True)

    if options.noinstall:
        io.out(_("Not installing GRUB!"))
        lines = grub.newgrubentries(options.include and options.mbr)
        io.out(_("Boot entries:"))
        for line in lines.splitlines():
            io.out("  >  %s" % line, True)
    else:
        io.out(_("Installing GRUB!"))
        r = grub.install(options.mbr, options.include)
        if r:
            io.out(r)
        else:
            errout(_("GRUB installation failed"))
            sys_quit(2)

    sys_quit(0)
"""
