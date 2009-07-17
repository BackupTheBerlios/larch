# stage.py - base class for stages of the installer
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
# 2009.03.23

import traceback

class StageBase:
    """The (main) base class for the stages of the installer, providing the
    basic framework. Note that the 'run' method is called within the
    background thread, so any interaction with the gui is handled by
    means of idle-calls and 'threading.Event' based waiting.
    Each installation stage has its own sub-class of this one.
    """
    def __init__(self, name):
        self.stagename = name


    def getHelp(self):
        return _("Sorry, I'm afraid there is at present no information"
                " for this stage.")

#TODO:
# Where to enable and disable interaction with the stage list and ok button.
# Maybe also the cancel burron.
    def run(self):
        """Run the stage. In order to cope with interrupts from the main
        thread, the variable install.interrupt is used. In the case of
        a detected error, install.error should be set to an appropriate
        message, and install.interrupt to "#ERROR". The cancel button
        should set install.interrupt to "#CANCEL".
        """
        # Clear execution interrupted flag and error message
        install.interrupt = None
        install.error = None
        # Set default continuation code (to determine which stage
        # should follow)
        self.continuation = 0

        try:
            # Show 'busy' widget and disable interaction:
            mainWindow.idle_setWidget("Transition", enable=False)

            # Run stage initialization method
            self.init()
            if install.interrupt:
                if install.interrupt == "#CANCEL":
                    install.error = _("You cancelled the initialization of "
                                "stage '%s'.") % self.stagename
                return

            # Queue an idle-call to show the stage's gui and then wait
            # for the OK button to be pressed. As this is running in the
            # background thread, it won't interfere with gui interaction.
            mainWindow.idle_setWidget(self.stagename, enable=True)
            while True:
                self.wait()
                if install.interrupt == "#CANCEL":
                    if install.showWarning(
                            _("Do  you want to quit the installer?"),
                            _("Quit larchin?")):
                        install.interrupt == "#QUIT"
                        return
                    else:
                        install.interrupt == None
                        continue
                elif install.interrupt:
                    return
                else:
                    break

            # Show widget for stage completion and disable interaction
            mainWindow.idle_setWidget(self.get_transit_widget(), enable=False)

            # Run stage completion method
            self.ok()
            if install.interrupt == "#CANCEL":
                install.error = _("You cancelled the execution of "
                            "stage '%s'.") % self.stagename

        except:
            if not install.error:
                install.error = traceback.format_exc()
                install.interrupt = "#BUG"


    ############
    # The following methods should be overriden as necessary to provide
    # the required behaviour for the stage.

    def init(self): pass


    def get_transit_widget(self): return "Transition"


    def ok(self): pass

    ############


