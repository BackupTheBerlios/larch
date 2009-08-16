#!/usr/bin/env python
#
# larchin - A hard-disk installer for Arch Linux and larch
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

import os, sys
import threading, traceback

basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append("%s/modules" % basedir)
sys.path.append("%s/modules/gtk" % basedir)

from install import installClass

from guimain import Larchin
from dialogs import popupError


#---------------------------
# Catch all unhandled errors.
#     This is probably not needed now that I have a try-except block in the
#     stages' 'run' method, but I can keep it here as a fallback.
def errorTrap(type, value, tb):
    etext = "".join(traceback.format_exception(type, value, tb))
    popupError(etext, _("This error could not be handled."))
    if initialized:
        try:
            install.tidyup()
        except:
            pass
    quit()

sys.excepthook = errorTrap
#---------------------------

import __builtin__
#def tr(s):
#    return s
#__builtin__._ = tr

import gettext
lang = os.getenv("LANG")
if lang:
    gettext.install('larchin', basedir+'/i18n', unicode=1)

import traceback
initialized = False

transfer = False
if (len(sys.argv) == 1):
    target = None
elif (len(sys.argv) == 2):
    target = sys.argv[1]
else:
    popupError(_("Usage:\n"
        "          larchin.py \t\t\t\t # local installation\n"
        "          larchin.py target-address \t # remote installation\n"),
        _("Bad arguments"))
    quit()

def plog(text):
    """A function to log information from the program.
    """
    #print text
    mainWindow.idle_call(mainWindow.report, text)

__builtin__.plog = plog
__builtin__.basePath = basedir
__builtin__.errormessage = None

__builtin__.mainWindow = Larchin()

__builtin__.install = installClass(target)

initialized = True


from welcome import Stage as s_welcome
from ntfs import Stage as s_ntfs
from disks import Stage as s_disks
from partitions import Stage as s_partitions
from partmanu import Stage as s_partmanu
from swaps import Stage as s_swaps
from selpart import Stage as s_selpart
from confirm import Stage as s_confirm
from rootpw import Stage as s_rootpw
from grub import Stage as s_grub
from end import Stage as s_end
from error import Stage as s_error

# Build a dictionary with the Stage classes and the stage continuations
# (which stage comes after the present one).
stages = {
        "Welcome":  (s_welcome, "NTFS"),
        "NTFS":     (s_ntfs, "Disks"),
        "Disks":    (s_disks, "Autopart", "ManuPart"),
        "Autopart": (s_partitions, "Confirm"),
        "ManuPart": (s_partmanu, "Swap"),
        "Swap":     (s_swaps, "Selp"),
        "Selp":     (s_selpart, "Confirm"),
        "Confirm":  (s_confirm, "Rootpw"),
        "Rootpw":   (s_rootpw, "Grub"),
        "Grub":     (s_grub, "Done"),
        "Done":     (s_end, "/"),
        "Error":    (s_error, "/")
    }

# This will associate stage names with the instances of the corresponding
# stage classes
__builtin__.stageobjects = {}

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Start the background thread and call 'run' on the first stage
#--------------------------------------------------------------

def runningThread():
    """Run the installation stages in a background thread and signal the
    main thread when it completes.
    """
    stage = "Welcome"
    while stage != "/":
        # See if stage object already initialized
        so = stageobjects.get(stage)
        if not so:
            # Create Stage instance for this stage.
            so = stages[stage][0](stage)
            stageobjects[stage] = so
        __builtin__.currentstage = so
        so.run()
        if so.interrupt:
            # Could be an error, or a skip(?), or a stage name
            if so.interrupt.startswith("#"):
                # An error or cancel has occurred. So far, the possibilities
                # are #ERROR, #CANCEL, #BUG and #QUIT.
                if so.interrupt == "#QUIT":
                    break
                if so.interrupt != "#SKIP":

                    __builtin__.errormessage = (so.error +
                            "\n\nPress OK to quit the installer, "
                            "or else select a stage from the list.\n"
                            "Note that there is no guarantee that you can "
                            "successfully run the selected stage.")

                    # Switch to the error stage.
                    stage = "Error"

            else:
                # It must be a stage switch request.
                stage = so.interrupt

                # Might want to untick things? It might not be easy to decide.
                continue

        else:
            mainWindow.idle_call(mainWindow.tick_stage, stage)

        # Get the next stage's name
        stage = stages[stage][so.continuation + 1]

    mainWindow.idle_call(thread_completed)

# - - - - - - - - - - - - - - - - - - -

def thread_completed():
    install.tidyup()
    mainWindow.exit()

pthread = threading.Thread(target=running_thread)
pthread.start()
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


mainWindow.mainLoop()



# What about generated .pyc files? Should the package include pre-compiled
# versions?
# Use module py_compile or compileall.
