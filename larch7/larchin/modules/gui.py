#!/usr/bin/env python
#
# gui.py
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
# 2009.10.24

import os, pwd
import json
import threading
from subprocess import Popen, PIPE
import locale


def chid():
    """Drop root privileges and reset the home-directory.
    """
    try:
        # Seems to fail when run from mc shell
        user = os.getlogin()
    except:
        # This will give the wrong name (root) if started via 'su -c'
        user = os.environ["USER"]

    pwdinfo = pwd.getpwnam(user)
    # pwdinfo[0] is user name
    # pwdinfo[2] is uid
    # pwdinfo[3] is gid
    # pwdinfo[5] is home dir
    os.environ["HOME"] = pwdinfo[5]
    os.environ["XAUTHORITY"]=pwdinfo[5] + "/.Xauthority"
    os.setgid(pwdinfo[3])
    os.setuid(pwdinfo[2])


class Ui:
    def __init__(self, guiexec):
        self.answer_event = threading.Event()
        self.answer_event.set()
        self.answer = None

        self.process_lock = threading.Lock()

        self.guiprocess = Popen(guiexec, cwd=base_dir, preexec_fn= chid,
                stdin=PIPE, stdout=PIPE)

        # Build the main window
        self.newwidget("Window", "larchin:", title="larchin",
                icon="images/larchin-icon.png", closesignal="$$$uiclose$$$")
        # - Header
        self.newwidget("Label", "larchin:i", image="images/larchin80.png")
        self.newwidget("Label", "larchin:h", html='<h1><span '
                'style="color:#c55500;">%s</span></h1>'
                % _("<i>larch</i> Installer"))
        self.newwidget("Button", "^larchin:showlog", text=_("View Log"),
                tt=_("This button switches to the log viewer"))
        self.newwidget("Button", "^larchin:docs", text=_("Help"),
                tt=_("This button switches to the documentation viewer"))
        self.newwidget("Button", "^larchin:cancel", text=_("Cancel"),
                tt=_("Stop the current action"))
#        self.newwidget("Button", "^larchin:quit", text=_("Quit"),
#                tt=_("Stop the current action and quit the program"))
        self.newwidget("Label", "larchin:stageheader", align="center")

        # - Main widget
        self.newwidget("Stack", "larchin:tabs", pages=[
                "tab:main", "tab:progress", "tab:log", "tab:doc"])

        self.newwidget("Stack", "larchin:stack", pages=[
                "page:welcome",
                "page:disks",
                "page:autopart",
                "page:install",
                "page:passwd",
                ])

        # - Footer
        self.newwidget("Button", "^larchin:goback", text=_("Go Back"),
                tt=_("Return to previous stage"))
        self.newwidget("Button", "^larchin:forward", text=_("OK"),
                tt=_("Execute any operations pending on this page and continue to next"))

        self.layout("larchin:", ["*VBOX*",
                ["*HBOX*", "larchin:i",
                    ["*VBOX*",
                        ["*HBOX*", "larchin:h", "*SPACE",
                            "larchin:showlog", "larchin:docs",],
#                            "larchin:cancel", "larchin:quit"],
                        "larchin:stageheader"]],
                "larchin:tabs",
                ])
        self.layout("tab:main", ["*VBOX*", "larchin:stack",
                ["*HBOX*", "larchin:goback", "*SPACE", "larchin:forward"]
                ])


    def go(self):
        # Build the documentation viewer
        self.docViewer = DocViewer()
        # A popup window for reporting on progress of lengthier operations
        self.progressPopup = ProgressPopup()
        command.addconnections([
                ("pp:hide*clicked", self.progressPopup.done),
                ("log:hide*clicked", self._hidelog),
                ("larchin:showlog*clicked", self._showlog),
                ("doc:hide*clicked", self._hidedocs),
                ("larchin:docs*clicked", self._showdocs),
                ("log:clear*clicked", plog),
            ])
        self.runningtab(0)
        self.command("larchin:.show")


    def getline(self):
        return self.guiprocess.stdout.readline()


    def command(self, cmd, *args):
        """Send a command to the user interface.
        The command is of the form 'widget.method', 'args' is the
        list of arguments. The argument list is encoded as json for
        transmission.
        """
        c = "!" + cmd
        if args:
            c += " " + json.dumps(args)
        self.sendui(c)


    def asknowait(self, cmd, signal, *args):
        """Send a request for information to the user interface.
        The command is of the form 'widget.method', 'args' is the
        list of arguments. The argument list is encoded as json for
        transmission.
        signal is the name of the signal to be sent by the ui to return
        the result of the enquiry.
        """
        c = "?%s:%s" % (signal, cmd)
        if args:
            c += " " + json.dumps(args)
        self.sendui(c)
        return None


    def ask(self, cmd, *args):
        """Send a request for information to the user interface.
        To be used in the background thread (only '&'-signals!).
        The command is of the form 'widget.method', 'args' is the
        list of arguments. The argument list is encoded as json for
        transmission.
        Wait for the answer and return it as result.
        """
        c = "?:" + cmd
        if args:
            c += " " + json.dumps(args)
        if not self.answer_event.is_set():
            fatal_error(_("ui not ready for enquiry:\n") + c)
        self.answer = None
        self.answer_event.clear()
        self.sendui(c)
        self.answer_event.wait()
        return self.answer


    def response(self, text):
        l, r = text.split(":", 1)
        a = json.loads(r)
        if l:
            command.runsignal(l, a)
        else:
            if self.answer_event.is_set():
                fatal_error(_("Unexpected response from ui:\n") + text)
            self.answer = a
            self.answer_event.set()


    def newwidget(self, wtype, wname, **args):
        self.sendui("%%%s %s %s" % (wtype, wname, json.dumps(args)))


    def layout(self, wname, ltree):
        self.sendui("$%s %s" % (wname, json.dumps(ltree)))


    def sendui(self, line):
        """Send a text line to the user interface process.
        """
        self.process_lock.acquire()
        try:
            self.guiprocess.stdin.write("%s\n" % line)
        except:
            errout("ui dead (%s)\n" % line)
        self.process_lock.release()


    def infoDialog(self, message, title=None, async=""):
        if title == None:
            title = _("Information")
        if async:
            return self.asknowait("infoDialog", async, message, title)
        return self.ask("infoDialog", message, title)


    def confirmDialog(self, message, title=None, async=""):
        if title == None:
            title = _("Confirmation")
        if async:
            return self.asknowait("confirmDialog", async, message, title)
        return self.ask("confirmDialog", message, title)


    def error(self, message, title=None, fatal=False):
        if title == None:
            title = _("Error")
        self.command("errorDialog" if fatal else "warningDialog",
            message, title)


    def busy(self):
        self.busywidget = "larchin:stack"
        self.command("larchin:forward.enable", False)
        self.command("larchin:goback.enable", False)
        self.command("larchin:.busy", self.busywidget, True)
        self.command("larchin:cancel.enable", True)


    def completed(self, ok):
        # 'ok' is not used here, but might be in the console interface
        self.command("larchin:cancel.enable", False)
        self.command("larchin:.busy", self.busywidget, False)
        self.command("larchin:goback.enable", True)
        self.command("larchin:forward.enable", True)


    def set_stageheader(self, text):
        self.command("larchin:stageheader.x__html",
                '<h2><span style="color:#55c500;">%s</span></h2>'
                % text)


    def formattable(self, headers, rows):
        """Build a html table from the given information.
        """
        html = '<table cellpadding="5" border="1">'
        html += '\n  <tr><th>%s</th></tr>' % '</th><th>'.join(headers)
        for r in rows:
            html += '\n  <tr><td>%s</td></tr>' % '</td><td>'.join(r)
        return html + '\n</table>'


    def _hidelog(self):
        self.runningtab()

    def _showlog(self):
        self.runningtab(2)

    def _hidedocs(self):
        self.runningtab()

    def _showdocs(self):
        self.runningtab(3)

    def runningtab(self, i=-1):
        if i < 0:
            i = self.maintab
        elif i < 2:
            self.maintab = i
        self.command("larchin:tabs.set", i)



class Logger:
    def __init__(self):
#TODO: This is experimental - it is intended to work around problems arising
#      when the system encoding is not utf8.
        self.encoding = locale.getdefaultlocale()[1]
        if self.encoding == "UTF8":
            self.encoding = None

        ui.newwidget("Label", "log:header",
            html='<h2>%s</h2><p>%s</p>' % (_("Low-level Command Logging"),
            _("Here you can follow the detailed, low-level progress"
            " of the commands.")))
        ui.newwidget("TextEdit", "log:text", ro=True)
        ui.newwidget("Button", "^log:clear", text=_("Clear"))
        ui.newwidget("Button", "^log:hide", text=_("Hide"))

        ui.layout("tab:log", ["*VBOX*", "log:header",
                ["*HBOX*", "log:text",
                    ["*VBOX*", "log:clear", "log:hide", "*SPACE"]]])

    def clear(self):
        ui.command("log:text.x__text")

    def addLine(self, line):
#TODO: This line is experimental - it is intended to work around problems arising
#      when the system encoding is not utf8.
        if self.encoding:
            line = line.decode(self.encoding, "replace").encode("UTF8")
        ui.command("log:text.append_and_scroll", line)

    def undo(self):
        ui.command("log:text.undo")

    def quit(self):
        return


class DocViewer:
    def __init__(self):
        ui.newwidget("Label", "doc:header",
            html='<h2>%s</h2>' % _("Documentation"))
        ui.newwidget("HtmlView", "doc:content")
        ui.newwidget("Button", "^doc:hide", text=_("Hide"))

        ui.layout("tab:doc", ["*VBOX*", "doc:header",
                ["*HBOX*", "doc:content",
                    ["*VBOX*", "doc:hide", "*SPACE"]]])


class ProgressPopup:
    def __init__(self):
        self.max = 0
        ui.newwidget("Label", "pp:header",
            html='<h2>%s</h2>' % _("Progress Report"))
        ui.newwidget("TextEdit", "pp:text", ro=True)
        ui.newwidget("Frame", "pp:extra")
        ui.newwidget("Label", "pp:le")
        ui.newwidget("LineEdit", "pp:info", ro=True)
        ui.newwidget("Button", "^pp:hide", text=_("OK"))
        ui.newwidget("ProgressBar", "pp:pbar")
        ui.layout("tab:progress", ["*VBOX*", "pp:header",
                "pp:text",
                "pp:pbar",
                "pp:extra",
                ["*HBOX*", "larchin:cancel", "*SPACE", "pp:hide"]])
        ui.layout("pp:extra", ["*HBOX*", ["*SPACE", 300],
                "pp:le", "pp:info"])

    def start(self):
        ui.command("pp:hide.enable", False)
        self.hide_extra()
        ui.command("pp:text.x__text")
        self.start_percent()
        ui.runningtab(1)

    def add(self, line):
        ui.command("pp:text.append_and_scroll", line)

    def show_extra(self, text):
        ui.command("pp:le.x__text", text)
        ui.command("pp:extra.setVisible", True)

    def hide_extra(self):
        ui.command("pp:extra.setVisible", False)

    def set_info(self, text):
        ui.command("pp:info.x__text", text)

    def set_percent(self, value, max=0):
        if max != self.max:
            self.start_percent(max, value)
        elif self.max > 0:
            ui.command("pp:pbar.set", value)

    def start_percent(self, max=0, start=0):
        self.max = max if max >= 0 else 0
        ui.command("pp:pbar.x__max", self.max)
        ui.command("pp:pbar.set", start)
        self.percent = start

    def end(self):
        if self.max == 0:
            self.max = 100
            ui.command("pp:pbar.x__max", self.max)
        ui.command("pp:pbar.set", self.max)
        ui.command("pp:hide.enable", True)

    def done(self):
        ui.runningtab(0)
