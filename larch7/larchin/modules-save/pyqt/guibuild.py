#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# guibuild.py
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
# 2009.10.03

"""Build a gui from a layout description.
"""

import os, sys, traceback
from PyQt4 import QtGui, QtCore
import json

#++++++++++++++++++++++++++++++++++++++++++++++++++++
#TODO
# Add more widgets
# Add more attribute handling
# Add more signal handling

#----------------------------------------------------

def debug(text):
    sys.stderr.write("GUI: %s\n" % text)
    sys.stderr.flush()


# Widget classes
class TopLevel:
    """This class cannot be used directly (it must be subclassed) because
    it doesn't set 'self.widget' itself, this must be set before
    calling this '__init__'.
    """
    def __init__(self, title, icon):
        self.layout = QtGui.QVBoxLayout()                   #qt
        self.widget.setLayout(self.layout)                  #qt
        self.widget.setWindowTitle(title)                   #qt
        if icon:
            app.setWindowIcon(QtGui.QIcon(icon))            #qt

    def add_widget(self, wl):
        """Add the widget/layout to the top level window.
        """
        if isinstance(wl, QtGui.QWidget):                   #qt
            self.layout.addWidget(wl)                       #qt
        elif isinstance(wl, SPACE):                         #qt
            if wl.size:                                     #qt
                self.layout.addSpacing(wl.size)             #qt
            self.layout.addStretch()                        #qt
        else:                                               #qt
            self.layout.addLayout(wl)                       #qt

    def busy(self, widget, on):
        w = guiapp.widgets[widget]
        if on:
            # doesn't work:
            #w.setCursor(QtCore.Qt.BusyCursor)
            app.setOverrideCursor(QtCore.Qt.BusyCursor)     #qt
            w.setEnabled(False)                             #qt
        else:
            #w.unsetCursor()
            app.restoreOverrideCursor()                     #qt
            w.setEnabled(True)                              #qt

    def setVisible(self, on=True):
        self.widget.setVisible(on)                          #qt

    def x_set_size(self, w_h):
        w, h = [int(i) for i in w_h.split("_")]
        self.widget.resize(w, h)                            #qt

    def getSize(self):
        s = self.widget.size()                              #qt
        return "%d_%d" % (s.width(), s.height())


class Widget(QtGui.QWidget):                                #qt
    """This is needed to trap window closing events.
    """
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)                #qt
        self.trapclose = None

    def closeEvent(self, event):                            #qt
        if self.trapclose == True:
            event.ignore()                                  #qt
            return
        elif self.trapclose and self.trapclose(event):      #qt
            event.ignore()
            return
        QtGui.QWidget.closeEvent(self, event)               #qt


class Window(TopLevel):
    def __init__(self, title, icon=None):
        self.widget = Widget()                              #qt
        TopLevel.__init__(self, title, icon)


class Dialog(TopLevel):
    def __init__(self, title, icon=None):
        self.widget = QtGui.QDialog()                       #qt
        TopLevel.__init__(self, title, icon)

    def showmodal(self):
        return self.widget.exec_() == QtGui.QDialog.Accepted    #qt


class DialogButtons(QtGui.QDialogButtonBox):                #qt
    def __init__(self, *args):
        buttons = 0
        for a in args:
            try:
                b = getattr(QtGui.QDialogButtonBox, a)      #qt
                assert isinstance(b, int)                   #qt
                buttons |= b                                #qt
            except:
                gui_warning(_("Unknown Dialog button: %s") % a)
        QtGui.QDialogButtonBox.__init__(self, buttons)      #qt

    def _connect(self, widgettree):
        self._dialog = widgettree.mainwidget.widget
        self.connect(self, QtCore.SIGNAL("clicked(QAbstractButton *)"), #qt
                self._clicked)                              #qt

    def _clicked(self, button):                             #qt
        if self.buttonRole(button) == self.AcceptRole:      #qt
            self._dialog.accept()                           #qt
        else:
            self._dialog.reject()                           #qt


def textLineDialog(label=None, title=None, text="", pw=False):
    if label == None:
        label = _("Enter the value here:")
    if title == None:
        title = _("Enter Information")
    if pw:
        echo = QtGui.QLineEdit.Password                     #qt
    else:
        echo = QtGui.QLineEdit.Normal                       #qt
    result, ok = QtGui.QInputDialog.getText(None,           #qt
            title, label, echo, text)                       #qt
    return (ok, unicode(result))


def confirmDialog(message, title=None):
    if title == None:
        title = _("Confirmation")
    return (QtGui.QMessageBox.question(None, title, message,
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel) ==
            QtGui.QMessageBox.Yes)


def infoDialog(message, title=None):
    if title == None:
        title = _("Information")
    QtGui.QMessageBox.information(None, title, message)


fileDialogDir = "/"
def fileDialog(message, start=None, title=None, dir=False, create=False, filter=None):
    # filter is a list: first a textual description, then acceptable glob filenames
    global fileDialogDir
    if not start:
        start = fileDialogDir
    dlg = QtGui.QFileDialog(None, message, start)           #qt
    if title:
        dlg.setWindowTitle(title)                           #qt
    dlg.setReadOnly(not create)                             #qt
    if dir:
        dlg.setFileMode(dlg.Directory)                      #qt
    elif not create:
        dlg.setFileMode(dlg.ExistingFile)                   #qt
    if filter:
        dlg.setNameFilter("%s (%s)" % (filter[0], " ".join(filter[1:])))    #qt
    if dlg.exec_():
        path = str(dlg.selectedFiles()[0]).strip()
        if os.path.isdir(path):
            fileDialogDir = path
        elif os.path.isfile(path):
            fileDialogDir = os.path.dirname(path)
        return path
    else:
        return ""


class Stack(QtGui.QStackedWidget):                          #qt
    def __init__(self, args):
        QtGui.QStackedWidget.__init__(self)                 #qt
        self.x_mywidgets = {}

        for page in args:
            pw = _Page()                                    #qt
            self.addWidget(pw)                              #qt
            pw.name = page                                  #qt
            self.x_mywidgets[page] = pw                     #qt

    def set(self, index=0):
        self.setCurrentIndex(index)                         #qt


class Notebook(QtGui.QTabWidget):                           #qt
    s_default = "changed"
    s_signals = {
            "changed": "currentChanged(int)"                #qt
        }
    def __init__(self, args):
        QtGui.QTabWidget.__init__(self)                     #qt
        self.x_tabs = []
        self.x_mywidgets = {}

        for tab in args:
            tname = tab[0]
            tw = _Page()                                    #qt
            self.addTab(tw, (tab[1]))                       #qt
            tw.name = tname                                 #qt
            self.x_mywidgets[tname] = tw                    #qt

            self.x_tabs.append([tname, tw])

    def set(self, index=0):
        self.setCurrentIndex(index)                         #qt

    def enableTab(self, index, on):
        self.setTabEnabled(index, on)                       #qt

class _Page(QtGui.QWidget):                                 #qt
    def __init__(self):                                     #qt
        QtGui.QWidget.__init__(self)                        #qt


class Frame(QtGui.QGroupBox):                               #qt
    def __init__(self, text="", format=None):
        if format:
            text = format.replace("$", text)
        QtGui.QGroupBox.__init__(self, text)                #qt

    def enable(self, on):
        self.setEnabled(on)                                 #qt


class OptionalFrame(Frame):                                 #qt
    s_default = "toggled"
    s_signals = {
            "toggled": "toggled(bool)"                      #qt
        }
    def __init__(self, text=""):                            #qt
        Frame.__init__(self, text)                          #qt
        self.setCheckable(True)                             #qt
        self.setChecked(False)                              #qt

    def enable(self, on):
        self.setChecked(on)                                 #qt

    def enable_hack(self):                                  #qt
        if not self.isChecked():                            #qt
            self.setChecked(True)                           #qt
            self.setChecked(False)                          #qt

    def frameEnable(self, on):
        self.setEnabled(on)                                 #qt


class Label(QtGui.QLabel):                                  #qt
    def __init__(self, text="", format=None):
        QtGui.QLabel.__init__(self)                         #qt
        self.format = format
        if text:
            self.set(text)

    def set(self, text):
        if self.format:
            text = self.format.replace("$", text)
        self.setText(text)                                  #qt

    def x_set_align(self, pos):
        if pos == "center":
            a = QtCore.Qt.AlignCenter                       #qt
        else:
            a = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter   #qt
        self.setAlignment(a)                                #qt


class Button(QtGui.QPushButton):                            #qt
    s_default = "clicked"
    s_signals = {
            "clicked": "clicked()"                          #qt
        }
    def __init__(self, text="", format=None):
        if format:
            text = format.replace("$", text)
        QtGui.QPushButton.__init__(self, text)              #qt

    def enable(self, on):
        self.setEnabled(on)                                 #qt


class ToggleButton(QtGui.QPushButton):                      #qt
    s_default = "toggled"
    s_signals = {
            "toggled": "toggled(bool)"                      #qt
        }
    def __init__(self, text="", format=None):
        if format:
            text = format.replace("$", text)
        QtGui.QPushButton.__init__(self, text)              #qt
        self.setCheckable(True)                             #qt

    def set(self, on):
        self.setChecked(on)                                 #qt


class CheckBox(QtGui.QCheckBox):                            #qt
    # A bit of work is needed to get True/False state       #qt
    # instead of 0/1/2                                      #qt
    s_default = "toggled"
    s_signals = {
            "toggled": "stateChanged(int)"                  #qt
        }
    def __init__(self, text="", format=None):
        if format:
            text = format.replace("$", text)
        QtGui.QCheckBox.__init__(self, text)                #qt

    def set(self, on):
        self.setCheckState(2 if on else 0)                  #qt

    def active(self):
        return self.checkState() != QtCore.Qt.Unchecked     #qt

    def s_toggled(self, state):                             #qt
        """Convert the argument to True/False.
        """                                                 #qt
        return (state != QtCore.Qt.Unchecked,)              #qt

    def enable(self, on):
        self.setEnabled(on)                                 #qt


class RadioButton(QtGui.QRadioButton):                      #qt
    s_default = "toggled"
    s_signals = {
            "toggled": "toggled(bool)"                      #qt
        }
    def __init__(self, text="", format=None):
        if format:
            text = format.replace("$", text)
        QtGui.QPushButton.__init__(self, text)              #qt

    def set(self, on):
        self.setChecked(on)                                 #qt

    def active(self):
        return self.isChecked()                             #qt

    def enable(self, on):
        self.setEnabled(on)                                 #qt


class ComboBox(QtGui.QComboBox):                            #qt
    s_default = "changed"
    s_signals = {
            "changed": "currentIndexChanged(int)" ,         #qt
            "changedstr": "currentIndexChanged(const QString &)"    #qt
        }
    def __init__(self):
        QtGui.QComboBox.__init__(self)                      #qt

    def set(self, items, index=0):
        self.blockSignals(True)
        self.clear()                                        #qt
        if items:
            self.addItems(items)                            #qt
            self.setCurrentIndex(index)                     #qt
        self.blockSignals(False)


class ListChoice(QtGui.QListWidget):                        #qt
    s_default = "changed"
    s_signals = {
            "changed": "currentRowChanged(int)" ,           #qt
        }
    def __init__(self):
        QtGui.QListWidget.__init__(self)                    #qt

    def set(self, items, index=0):
        self.blockSignals(True)
        self.clear()                                        #qt
        if items:
            self.addItems(items)                            #qt
            self.setCurrentRow(index)                       #qt
        self.blockSignals(False)


class List(QtGui.QTreeWidget):                              #qt
    # Only using top-level items
    s_default = "select"
    s_signals = {
            "select": "itemSelectionChanged()" ,            #qt
        }
    def __init__(self, selectionmode=""):
        QtGui.QTreeWidget.__init__(self)                    #qt
        self.mode = selectionmode
        if selectionmode == "None":
            self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)  #qt
        elif selectionmode == "Single":
            self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection) #qt
        else:
            self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) #qt
        self.setRootIsDecorated(False)                      #qt

    def setHeaders(self, headers):                          #qt
        debug(repr(headers))
        self.setHeaderLabels(headers)                       #qt

    def set(self, items, index=0):                          #qt
        # Note that each item must be a tuple/list containing
        # entries for each column.
        self.clear()                                        #qt
        c = 0
        for i in items:
            debug(repr(i))
            item = QtGui.QTreeWidgetItem(self, i)           #qt
            self.addTopLevelItem(item)                      #qt
            if c == index:
                self.setCurrentItem(item)
            c += 1

    def compact(self):
        for i in range(self.columnCount()):                 #qt
            self.resizeColumnToContents(i)                  #qt

    def s_select(self):
        # Signal a selection change, passing the new selection list (indexes)
        s = [self.indexOfTopLevelItem(i) for i in self.selectedItems()] #qt
        if self.mode == "Single":
            return s
        else:
            return (s,)


class LineEdit(QtGui.QLineEdit):                            #qt
    s_default = "changed"
    s_signals = {
            "enter": "returnPressed()",                     #qt
            "changed": "textEdited(const QString &)"        #qt
        }
    def __init__(self, text="", format=None):
        self.format = format
        QtGui.QLineEdit.__init__(self)                      #qt
        if text:
            self.set(text)

    def set(self, text=""):
        if self.format:
            text = format.replace("$", text)
        self.setText(text)                                  #qt

    def get(self):
        return unicode(self.text())                         #qt

    def x_set_readonly(self, ro):
        self.setReadOnly(ro == "true")                      #qt


class CheckList(QtGui.QWidget):                             #qt
    def __init__(self, text="", format=None):
        if format:
            text = format.replace("$", text)
        QtGui.QWidget.__init__(self)                        #qt
        l = QtGui.QVBoxLayout(self)                         #qt
        if text:                                            #qt
            l.addWidget(QtGui.QLabel(text))                 #qt
        self.widget = QtGui.QListWidget()                   #qt
        l.addWidget(self.widget)                            #qt

    def checked(self, index):
        return (self.widget.item(index).checkState() ==     #qt
                QtCore.Qt.Checked)                          #qt

    def set(self, items):
        self.widget.blockSignals(True)                      #qt
        self.widget.clear()                                 #qt
        if items:
            for s, c in items:
                wi = QtGui.QListWidgetItem(s, self.widget)  #qt
                wi.setCheckState(QtCore.Qt.Checked if c     #qt
                        else QtCore.Qt.Unchecked)           #qt
        self.blockSignals(False)                            #qt


class TextEdit(QtGui.QTextEdit):                            #qt
    def __init__(self, ro=""):
        QtGui.QTextEdit.__init__(self)                      #qt
        if ro:
            self.setReadOnly(True)                          #qt

    def set(self, text=""):
        self.setText(text)                                  #qt

    def append_and_scroll(self, text):
        self.append(text)                                   #qt
        self.ensureCursorVisible()                          #qt

    def get(self):
        return unicode(self.toPlainText())                  #qt

    def undo(self):
        QtGui.QTextEdit.undo(self)                          #qt


class HtmlView(QtGui.QTextBrowser):                         #qt
    def __init__(self):
        QtGui.QTextBrowser.__init__(self)                   #qt

    def set(self, content):
        self.setHtml(content)                               #qt


# Layout classes
class _BOX:
    def __init__(self, items):
        self.x_children = items

    def add_children(self, widgets):
        for c in self.x_children:
            wl = widgets[c]
            if isinstance(wl, QtGui.QWidget):               #qt
                self.addWidget(wl)                          #qt
            elif isinstance(wl, SPACE):                     #qt
                if wl.size:                                 #qt
                    self.addSpacing(wl.size)                #qt
                self.addStretch()                           #qt
            else:                                           #qt
                self.addLayout(wl)                          #qt


class VBOX(QtGui.QVBoxLayout, _BOX):                        #qt
    def __init__(self, items):
        QtGui.QVBoxLayout.__init__(self)                    #qt
        _BOX.__init__(self, items)                          #qt


class HBOX(QtGui.QHBoxLayout, _BOX):                        #qt
    def __init__(self, items):
        QtGui.QHBoxLayout.__init__(self)                    #qt
        _BOX.__init__(self, items)                          #qt


class GRID(QtGui.QGridLayout):                              #qt
    def __init__(self, *rows):
        QtGui.QGridLayout.__init__(self)                    #qt
        self.x_children = rows

    def add_children(self, widgets):
        y = -1
        for row in self.x_children:
            y += 1
            x = -1
            for col in row:
                x += 1
                wl = widgets.get(col)
                if not wl:
                    continue
                # Determine the row and column spans
                x1 = x + 1
                while (x1 < len(row)) and (row[x1] == "-"):
                    x1 += 1
                y1 = y + 1
                while ((y1 < len(self.x_children)) and
                        (self.x_children[y1][x] == "|")):
                    y1 += 1

                if isinstance(wl, QtGui.QWidget):           #qt
                    self.addWidget(wl, y, x, y1-y, x1-x)    #qt
                else:                                       #qt
                    self.addLayout(wl, y, x, y1-y, x1-x)    #qt


class SPACE:                                                #qt
    def __init__(self, size=0):                             #qt
        self.size = size                                    #qt


class HLINE(QtGui.QFrame):                                  #qt
    def __init__(self):
        QtGui.QFrame.__init__(self)                         #qt
        self.setFrameShape(QtGui.QFrame.HLine)              #qt


class VLINE(QtGui.QFrame):                                  #qt
    def __init__(self):
        QtGui.QFrame.__init__(self)                         #qt
        self.setFrameShape(QtGui.QFrame.VLine)              #qt


class Signal:
    """Each instance represents a single connection.
    """
    def __init__(self, source, signal, name=None, tag=None):
        """'source' is the widget which initiates the signal.
        'signal' is the name of the signal.
        If 'name' is given, the signal will get this as its name,
        and this name may be used for more than one connection.
        Otherwise the name is built as 'source_signal' and may
        only be used once.
        'tag' is passed as the first argument to the signal handler.
        Normal arguments of the signal follow.
        """
        self.signame = signal
        sig = source.s_signals.get(signal)
        if not sig:
            gui_warning(_("Signal '%s' is not defined for '%s'.")
                        % (signal, source.x_name))
            return
        if name:
            l = guiapp.connections.get(name, [])
        else:
            l = self
            name = "%s*%s" % (source.x_name, signal)
            if guiapp.connections.has_key(name):
                gui_warning(_("Signal '%s' is defined more than once.")
                        % name)
                return
        self.name = name
        self.tag = tag
        try:
            self.convert = getattr(source, "s_%s" % signal)
        except:
            self.convert = None
        if QtCore.QObject.connect(source, QtCore.SIGNAL(sig), self.signal): #qt
            if l != self:
                l.append(self)
            guiapp.connections[name] = l
        else:
            gui_warning(_("Signal '%s' couldn't be connected.")
                    % name)

    def signal(self, *args):
        if self.convert:
            args = self.convert(*args)
        guiapp.send("^", "%s %s" % (self.name, json.dumps([self.tag, args])))

#    def disconnect(self):
#        ???


class GuiApp:
    """This class represents an application gui, possibly with more than
    one top level window, these being defined in layout files.
    """
    def __init__(self, qtapp):
        global app, guiapp
        app = qtapp
        guiapp = self
        self.windows = []
        self.connections = {}
        self.widgets = {}


    def init(self, windowfiles, dir=None):
        if not dir:
            dir = os.path.dirname(__file__)
        for f in windowfiles:
            d = {}
            execfile("%s/%s" % (dir, f), globals(), d)
            self.windows.append(WidgetTree(d))


    def addwidget(self, fullname, wo):
        if self.widgets.has_key(fullname):
            gui_error(_("Attempted to define widget '%s' twice.") % fullname)
        self.widgets[fullname] = wo


    def show(self, windowname):
        self.widgets[windowname].setVisible()


    def new_line(self, line):
        """An input line has been received.
        Lines starting with '!' are method calls to an exported widget,
        with no result. They have the form
          '!widget.method [arg1, arg2, ...]'
        where the argument list is json-encoded. If there are no arguments
        the square brackets needn't be present.
        Lines starting with '?' are similar, but a return value is expected.
        This is returned as '@' followed by the json-encoded result.
        """
        line = str(line).rstrip()

        #DEBUG
        #sys.stderr.write(line+'\n')
        #sys.stderr.flush()

        if line[0] in ["!", "?"]:
            wma = line[1:].split(None, 1)
            cmd = specials_table.get(wma[0])
            if not cmd:
                w, m = wma[0].split(".")
                wo = self.widgets[w]
                cmd = getattr(wo, m)
            if len(wma) > 1:
                res = cmd(*json.loads(wma[1]))
            else:
                res = cmd()

            if line[0] == "?":
                self.send("@", json.dumps(res))

        else:
            self.got(line)


#TODO: But I'm not very sure what this should do.
    def got(self, line):
        """Reimplement this in a sub-class to do something else?
        """
        self.send("=", line)


    def send(self, mtype, line):
        """Reimplement this in a sub-class to do something else?
        """
        sys.stdout.write("%s%s\n" % (mtype, line))
        sys.stdout.flush()


    def answer(self, obj):
        self.send("@", json.dumps(obj))


class WidgetTree:
    """This class represents one top level window.
    """
    def __init__(self, info):
        self.namespace = info.get("Namespace", "")

        # Create all widgets
        wlist = info["Widgets"]
        main = wlist[0][1]

        self.widgets = {}
        for w in wlist:
            wtype = w[0]
            wname = w[1]
            if wname[0] == "^":
                wname = wname[1:]
                connect = True
            else:
                connect = False
            fullname = self.namespace + wname
            #sys.stderr.write(">>>%s\n" % fullname)
            if wtype[0] == "*":
                wo = widget_table[wtype[1:]](*w[2:])
                guiapp.addwidget(fullname, wo)
            else:
                wo = widget_table[wtype](*w[2:])
            self.widgets[wname] = wo
            wo.x_name = fullname
            if connect:
                Signal(wo, wo.s_default)

            # The widget may itself have created widgets that need including
            try:
                self.widgets.update(wo.x_mywidgets)
            except:
                pass

        self.mainwidget = self.widgets[main]


        # Do the layouts in two stages to allow definition-after-use
        layout = info.get("Layout", [])
        pending = []
        for l in layout:
            ltype = l[0]
            if ltype[0] == "+":
                pending.append(l)

            else:
                lname = l[1]
                lo = layout_table[ltype](*l[2:])
                lo.x_name = lname
                if hasattr(lo, "x_children"):
                    pending.append(("+", lo))
                self.widgets[lname] = lo

        for p in pending:
            ptype = p[0]
            if ptype == "+":
                p[1].add_children(self.widgets)

            elif ptype == "+MAIN":
                for wl in p[1]:
                    self.mainwidget.add_widget(self.widgets[wl])

            elif ptype == "+LAYOUT":
                self.widgets[p[1]].setLayout(self.widgets[p[2]])

            else:
                gui_error(_("Unknown node type: %s") % ptype)
                # fatal


        # Handle tooltips
        tooltips = info.get("Tooltips", [])
        # This is a list of [widget, text] pairs
        for w, t in tooltips:
            widget = self.getwidget(w)
            if widget:
                widget.setToolTip(t)


        # Handle attributes
        attributes = info.get("Attributes", [])
        # This is a list of [widget, attribute, value] triplets
        for w, a, v in attributes:
            widget = self.getwidget(w)
            if not widget:
                continue
            setter = "x_set_" + a
            try:
                getattr(widget, setter)(v)
            except:
                # If there is no setter, just ignore it
                pass


        # Connect signals
        signals = info.get("Signals", [])
        # This is, in principle, a list of [widget, signal, arg] triplets,
        # but the 'arg' element may be missing. There may also be special
        # forms, e.g. for dealing with 'internal' connections.
        for conn in signals:
            if conn[0] == "+INTERNAL":
                source = self.getwidget(conn[1])
                if not source:
                    continue
                source._connect(self, *conn[2:])

            else:
                w = self.widgets.get(conn[0])
                Signal(w, *conn[1:])


    def getwidget(self, w):
        widget = self.widgets.get(w)
        if not widget:
            gui_warning(_("Unknown widget: %s") % w)
        return widget


#+++++++++++++++++++++++++++
# Error handling
def gui_error(message, title=None):
    if not title:
        title = _("Error")
    d = QtGui.QMessageBox.critical(None, title, message)    #qt
    app.exit(1)

def gui_warning(message, title=None):
    if not title:
        title = _("Warning")
    d = QtGui.QMessageBox.warning(None, title, message)     #qt
#---------------------------

#+++++++++++++++++++++++++++
# Catch all unhandled errors.
def errorTrap(type, value, tb):
    etext = "".join(traceback.format_exception(type, value, tb))
    gui_error(etext, _("This error could not be handled."))

sys.excepthook = errorTrap
#---------------------------

widget_table = {
    "Window": Window,
    "Dialog": Dialog,
    "DialogButtons": DialogButtons,
    "Notebook": Notebook,
    "Stack": Stack,
    "Frame": Frame,
    "Button": Button,
    "ToggleButton": ToggleButton,
    "RadioButton": RadioButton,
    "CheckBox": CheckBox,
    "Label": Label,
    "CheckList": CheckList,
    "List": List,
    "OptionalFrame": OptionalFrame,
    "ComboBox": ComboBox,
    "ListChoice": ListChoice,
    "LineEdit": LineEdit,
    "TextEdit": TextEdit,
    "HtmlView": HtmlView,
}

specials_table = {
    "textLineDialog": textLineDialog,
    "infoDialog": infoDialog,
    "confirmDialog": confirmDialog,
    "fileDialog": fileDialog,
}

layout_table = {
    "VBOX": VBOX,
    "HBOX": HBOX,
    "GRID": GRID,
    "VSPACE": SPACE,
    "HSPACE": SPACE,
    "VLINE": VLINE,
    "HLINE": HLINE,
}



#+++++++++++++++++++++++++++++++++++
# The input handler, a separate thread.

# Start input thread
class Input(QtCore.QThread):                                #qt
    def __init__(self, input, target):
        QtCore.QThread.__init__(self)                       #qt
        # It seems the argument must be a Qt type:
        self.lineReady = QtCore.SIGNAL("lineReady(QString)")    #qt
        self.input = input
        self.connect(self, self.lineReady, target)          #qt

    def run(self):
        while True:
            line = self.input.readline()
            if not line:        # Is this at all possible?
                return
            self.emit(self.lineReady, line)                 #qt
#---------------------------

