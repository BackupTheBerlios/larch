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
# 2009.12.10

import os, pwd
from uipi import Uipi
import locale


class Ui(Uipi):
    def __init__(self, guiexec):
        Uipi.__init__(self, backend=guiexec, cwd=base_dir)

        self.stagetext = None

        # Build the main window
        self.widget("Window", "larchin:", title="larchin", size="750_450",
                icon="images/larchin-icon.png", closesignal="$$$uiclose$$$")
        # - Header
        self.widget("Label", "larchin:i", image="images/larchin80.png")
        self.widget("Label", "larchin:h", html='<h1><span '
                'style="color:#c55500;">%s</span></h1>'
                % _("<i>larch</i> Installer"))
        self.widget("Button", "^larchin:showlog", text=_("View Log"),
                tt=_("This button switches to the log viewer"))
        self.widget("Button", "^larchin:docs", text=_("Help"),
                tt=_("This button switches to the documentation viewer"))
        self.widget("Button", "^larchin:cancel", text=_("Cancel"),
                tt=_("Stop the current action"))
#        self.widget("Button", "^larchin:quit", text=_("Quit"),
#                tt=_("Stop the current action and quit the program"))
        self.widget("Label", "larchin:stageheader", align="center")

        # - Main widget
        self.widget("Stack", "larchin:tabs", pages=["tab:main",
                "tab:progress", "tab:log", "tab:doc", "tab:edit"])

        self.widget("Stack", "larchin:stack", pages=[
                "page:welcome",
                "page:disks",
                "page:autopart",
                "page:install",
                "page:passwd",
                "page:grub",
                "page:done"
                ])

        # - Footer
        self.widget("Button", "^larchin:goback", text=_("Go Back"),
                tt=_("Return to previous stage"))
        self.widget("Button", "^&-larchin:forward", text=_("OK"),
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
                ["*HBOX*", "larchin:goback", "*SPACE", "&-larchin:forward"]
                ])

        self.setDisableWidgets("larchin:", ("&-larchin:forward",
                "larchin:goback", "larchin:stack"))


    def go(self):
        # Build the documentation viewer
        self.docViewer = DocViewer()
        # Build the editor
        self.editor = Editor()
        self.edit = self.editor.start
        # A popup window for reporting on progress of lengthier operations
        self.progressPopup = ProgressPopup()
        command.addconnections([
                ("pp:hide*clicked", self.progressPopup.done),
                ("log:hide*clicked", self.runningtab),
                ("larchin:showlog*clicked", self._showlog),
                ("doc:hide*clicked", self.runningtab),
                ("larchin:docs*clicked", self._showdocs),
                ("log:clear*clicked", plog),
                ("edit:ok*clicked", self.runningtab),
                ("edit:ok*clicked", self.editor.ok),
                ("edit:cancel*clicked", self.runningtab),
                ("edit:revert*clicked", self.editor.dorevert),
                ("edit:copy*clicked", self.editor.copy),
                ("edit:cut*clicked", self.editor.cut),
                ("edit:paste*clicked", self.editor.paste),
                ("edit:undo*clicked", self.editor.undo),
                ("edit:redo*clicked", self.editor.redo),
                ("$edit-done$", self.editor.sendtext),
            ])
        self.runningtab(0)
        self.command("larchin:.show")


    def sendsignal(self, sig, *args):
        #debug("SIG:" + sig + "---" + repr(args))
        if sig.endswith("-"):
            # This is to suppress appending to the pagehistory (used by
            # the 'Go Back' feature. Remove the '-'.
            sig = sig[:-1]
        elif sig.endswith("!"):
            # It is a page switch, and needs an extra argument
            command.pagehistory.append(sig)
            args = (True,) + (args)

        Uipi.sendsignal(self, sig, *args)


    def busy(self):
        # Override Uipi method
        self.command("larchin:cancel.enable", True)
        Uipi.busy(self)


    def unbusy(self, ok=True):
        # Override Uipi method
        # 'ok' is not used here, but might be in the console interface
        self.command("larchin:cancel.enable", False)
        Uipi.unbusy(self)


    def set_stageheader(self, text=None):
        # Delay setting if running progress tab
        if text == None:
            if self.stagetext != None:
                text = self.stagetext
                self.stagetext = None
            else:
                return
        elif (self.maintab != 0):
            self.stagetext = text
            return
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


    def _showlog(self):
        self.runningtab(2)

    def _showdocs(self):
        self.runningtab(3)

    def runningtab(self, i=-1):
        if i < 0:
            i = self.maintab
        elif i < 2:
            self.maintab = i
            if i == 0:
                self.set_stageheader()
        self.command("larchin:tabs.set", i)



class Logger:
    def __init__(self):
#TODO: This is experimental - it is intended to work around problems arising
#      when the system encoding is not utf8.
        self.encoding = locale.getdefaultlocale()[1]
        if self.encoding == "UTF8":
            self.encoding = None

        ui.widget("Label", "log:header",
            html='<h2>%s</h2><p>%s</p>' % (_("Low-level Command Logging"),
            _("Here you can follow the detailed, low-level progress"
            " of the commands.")))
        ui.widget("TextEdit", "log:text", ro=True)
        ui.widget("Button", "^log:clear", text=_("Clear"))
        ui.widget("Button", "^log:hide", text=_("Hide"))

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
        ui.widget("Label", "doc:header",
            html='<h2>%s</h2>' % _("Documentation"))
        ui.widget("HtmlView", "doc:content")
        ui.widget("Button", "^doc:hide", text=_("Hide"))

        ui.layout("tab:doc", ["*VBOX*", "doc:header",
                ["*HBOX*", "doc:content",
                    ["*VBOX*", "doc:hide", "*SPACE"]]])


class Editor:
    def __init__(self):
        ui.widget("Label", "edit:header",
            html='<h2>%s</h2>' % _("Editor"))
        ui.widget("Label", "edit:title")
        ui.widget("TextEdit", "edit:content")
        ui.widget("Button", "^edit:ok", text=_("OK"))
        ui.widget("Button", "^edit:cancel", text=_("Cancel"))
        ui.widget("Button", "^edit:revert", text=_("Revert"),
                tt=_("Restore the text to its initial state"))
        ui.widget("Button", "^edit:copy", text=_("Copy"))
        ui.widget("Button", "^edit:cut", text=_("Cut"))
        ui.widget("Button", "^edit:paste", text=_("Paste"))
        ui.widget("Button", "^edit:undo", text=_("Undo"))
        ui.widget("Button", "^edit:redo", text=_("Redo"))

        ui.layout("tab:edit", ["*VBOX*",
                ["*HBOX*", "edit:header", "*SPACE", "edit:title"],
                ["*HBOX*", "edit:content",
                    ["*VBOX*", "edit:copy", "edit:cut", "edit:paste",
                        "edit:undo", "edit:redo", "edit:revert",
                        "*SPACE", "edit:cancel", "edit:ok"]]])

    def start(self, title, endcall, text="", revert=None):
        ui.command("edit:title.x__text", title)
        self.endcall = endcall
        self.revert = revert
        try:
            self.text0 = revert() if text == None else text
        except:
            run_error("BUG: No revert function?")
        ui.command("edit:content.x__text", self.text0)
        ui.runningtab(4)

    def ok(self):
        ui.asknowait("edit:content.get", "$edit-done$")

    def sendtext(self, text):
        self.endcall(text)

    def dorevert(self):
        if self.revert:
            self.text0 = self.revert()
        ui.command("edit:content.x__text", self.text0)

    def copy(self):
        ui.command("edit:content.copy")

    def cut(self):
        ui.command("edit:content.cut")

    def paste(self):
        ui.command("edit:content.paste")

    def undo(self):
        ui.command("edit:content.undo")

    def redo(self):
        ui.command("edit:content.redo")


class ProgressPopup:
    def __init__(self):
        self.max = 0
        ui.widget("Label", "pp:header",
            html='<h2>%s</h2>' % _("Progress Report"))
        ui.widget("TextEdit", "pp:text", ro=True)
        ui.widget("Frame", "pp:extra")
        ui.widget("Label", "pp:le")
        ui.widget("LineEdit", "pp:info", ro=True)
        ui.widget("Button", "^pp:hide", text=_("OK"))
        ui.widget("ProgressBar", "pp:pbar")
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
