# welcome.py - first - 'welcome' - stage
#
# (c) Copyright 2008, 2009 Michael Towers <gradgrind[at]online[dot]de>
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
# 2009.03.23

from stagebase import StageBase

"""This is a really minimal subclass - it doesn't do anything except display
an introductory message, so I just supply a help message for extra information.
"""
class Stage(StageBase):
    def getHelp(self):
        return _("This installation program concentrates on just the most"
                " essential aspects of Arch Linux system installation: disk"
                " preparation, copying of the system data, generation of"
                " the initramfs, setting up the GRUB bootloader and setting"
                " the root password.\n"
                "The remaining configuration of the system can be performed"
                " before running this program. This is one advantage of"
                " installing from a 'live' system - the configuration can"
                " be set up and tested before installation.\n"
                "Configuration can of course also be performed later, on"
                " the running installed system, if you prefer.\n\n"
                "Simple graphical programs for setting the xorg keyboard"
                " layout (xkmap), for adding users (luser) and for setting"
                " the locale (localed) are available in the larch repository,"
                " and may be found in the 'system' category of the menu if"
                " they have been installed.\n\n"
                "Other useful sources of information concerning"
                " installation are the Arch Linux Installation Guide, and"
                " the Arch Linux wiki, for example the Beginner's Guide.\n\n"
                "Click on the 'OK' button to start.")

