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
# 2009.10.18

"""Build a gui from a layout description.
"""

import os, sys, traceback, threading
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


# Widget Base Classes - essentially used as 'Mixins' >>>>>>>>>>>>>>>>
class WBase:
    def x__tt(self, text):
        """Set tooltip.
        """
        self.setToolTip(text)                               #qt

    def x__text(self, text=""):
        """Set widget text.
        """
        self.setText(text)                                  #qt

    def enable(self, on):
        """Enable/Disable widget. on should be True to enable the widget
        (display it in its normal, active state), False to disable it
        (which will normally be paler and non-interactive).
        """
        self.setEnabled(on)                                 #qt


class TopLevel:
    def busy(self, widget, on):
        w = guiapp.widgets[widget]
        if on:
            # doesn't work:
            #w.setCursor(QtCore.Qt.BusyCursor)
            guiapp.qtapp.setOverrideCursor(QtCore.Qt.BusyCursor) #qt
            w.setEnabled(False)                             #qt
        else:
            #w.unsetCursor()
            guiapp.qtapp.restoreOverrideCursor()            #qt
            w.setEnabled(True)                              #qt

    def setVisible(self, on=True):
        self.setVisible(on)                                 #qt

    def x__size(self, w_h):
        w, h = [int(i) for i in w_h.split("_")]
        self.resize(w, h)                                   #qt

    def x__icon(self, iconpath):
        guiapp.qtapp.setWindowIcon(QtGui.QIcon(iconpath))   #qt

    def x__title(self, text):
        self.setWindowTitle(text)                           #qt

    def getSize(self):
        s = self.size()                                     #qt
        return "%d_%d" % (s.width(), s.height())            #qt

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

class Window(QtGui.QWidget, TopLevel):                      #qt
    """This is needed to trap window closing events.
    """
    def __init__(self):
        QtGui.QWidget.__init__(self)                        #qt
        self.closesignal = ""

    def closeEvent(self, event):                            #qt
        if self.closesignal:
            guiapp.sendsignal(self.closesignal)
            event.ignore()                                  #qt
            return
        guiapp.send("/", "1")
        QtGui.QWidget.closeEvent(self, event)               #qt

    def x__closesignal(self, text):
        self.closesignal = text


class Dialog(QtGui.QDialog, TopLevel):
    def __init__(self):
        QtGui.QDialog.__init__(self)                        #qt

    def showmodal(self):
        return self.exec_() == QtGui.QDialog.Accepted       #qt


class DialogButtons(QtGui.QDialogButtonBox):                #qt
    def __init__(self, *args):
        buttons = 0
        for a in args:
            try:
                b = getattr(QtGui.QDialogButtonBox, a)      #qt
                assert isinstance(b, int)                   #qt
                buttons |= b                                #qt
            except:
                gui_warning("Unknown Dialog button: %s" % a)
        QtGui.QDialogButtonBox.__init__(self, buttons)      #qt

#TODO: there is no widgettree or mainwidget now ...
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
        label = "Enter the value here:"
    if title == None:
        title = "Enter Information"
    if pw:
        echo = QtGui.QLineEdit.Password                     #qt
    else:
        echo = QtGui.QLineEdit.Normal                       #qt
    result, ok = QtGui.QInputDialog.getText(None,           #qt
            title, label, echo, text)                       #qt
    return (ok, unicode(result))


def confirmDialog(message, title=None):
    if title == None:
        title = "Confirmation"
    return (QtGui.QMessageBox.question(None, title, message,        #qt
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel) ==    #qt
            QtGui.QMessageBox.Yes)                                  #qt


def infoDialog(message, title=None):
    if title == None:
        title = "Information"
    QtGui.QMessageBox.information(None, title, message)     #qt


#+++++++++++++++++++++++++++
# Error handling
def gui_error(message, title=None):
    if title == None:
        title = "Error"
    QtGui.QMessageBox.critical(None, title, message)        #qt
    guiapp.qtapp.exit(1)                                    #qt

def gui_warning(message, title=None):
    if title == None:
        title = "Warning"
    QtGui.QMessageBox.warning(None, title, message)         #qt

def onexcept(text):
    debug(traceback.format_exc())
    gui_error(text, "Exception")
#---------------------------

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
    def __init__(self):
        QtGui.QStackedWidget.__init__(self)                 #qt
        self.x_mywidgets = {}

    def x__pages(self, pages):
        for page in pages:
            pw = _Page()                                    #qt
            self.addWidget(pw)                              #qt
            pw.w_name = page
            self.x_mywidgets[page] = pw

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

    def x__tabs(self, tabs):
        for tab in tabs:
            tname = tab[0]
            tw = _Page()                                    #qt
            self.addTab(tw, (tab[1]))                       #qt
            tw.w_name = tname
            self.x_mywidgets[tname] = tw
            self.x_tabs.append([tname, tw])

    def set(self, index=0):
        self.setCurrentIndex(index)                         #qt

    def enableTab(self, index, on):
        self.setTabEnabled(index, on)                       #qt

class _Page(QtGui.QWidget):                                 #qt
    def __init__(self):                                     #qt
        QtGui.QWidget.__init__(self)                        #qt


class Frame(QtGui.QGroupBox, WBase):                        #qt
    def __init__(self):
        QtGui.QGroupBox.__init__(self)                      #qt

    def x__text(self, text):
        self.setTitle(text)                                 #qt


class OptionalFrame(Frame):                                 #qt
    s_default = "toggled"
    s_signals = {
            "toggled": "toggled(bool)"                      #qt
        }
    def __init__(self):                                     #qt
        Frame.__init__(self)                                #qt
        self.setCheckable(True)                             #qt
        self.setChecked(False)                              #qt

    def opton(self, on):
        self.setChecked(on)                                 #qt

    def enable_hack(self):                                  #qt
        if not self.isChecked():                            #qt
            self.setChecked(True)                           #qt
            self.setChecked(False)                          #qt


class Label(QtGui.QLabel, WBase):                           #qt
    def __init__(self):
        QtGui.QLabel.__init__(self)                         #qt

    def x__html(self, text):
        self.setText(text)                                  #qt

    def x__image(self, path):
        self.setPixmap(QtGui.QPixmap(path))                 #qt

    def x__align(self, pos):
        if pos == "center":
            a = QtCore.Qt.AlignCenter                       #qt
        else:
            a = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter   #qt
        self.setAlignment(a)                                #qt


class Button(QtGui.QPushButton, WBase):                     #qt
    s_default = "clicked"
    s_signals = {
            "clicked": "clicked()"                          #qt
        }
    def __init__(self):
        QtGui.QPushButton.__init__(self)                    #qt


class ToggleButton(QtGui.QPushButton, WBase):               #qt
    s_default = "toggled"
    s_signals = {
            "toggled": "toggled(bool)"                      #qt
        }
    def __init__(self):
        QtGui.QPushButton.__init__(self)                    #qt
        self.setCheckable(True)                             #qt

    def set(self, on):
        self.setChecked(on)                                 #qt


class CheckBox(QtGui.QCheckBox, WBase):                     #qt
    # A bit of work is needed to get True/False state       #qt
    # instead of 0/1/2                                      #qt
    s_default = "toggled"
    s_signals = {
            "toggled": "stateChanged(int)"                  #qt
        }
    def __init__(self):
        QtGui.QCheckBox.__init__(self)                      #qt

    def set(self, on):
        self.setCheckState(2 if on else 0)                  #qt

    def active(self):
        return self.checkState() != QtCore.Qt.Unchecked     #qt

    def s_toggled(self, state):                             #qt
        """Convert the argument to True/False.
        """                                                 #qt
        return (state != QtCore.Qt.Unchecked,)              #qt


class RadioButton(QtGui.QRadioButton, WBase):               #qt
    s_default = "toggled"
    s_signals = {
            "toggled": "toggled(bool)"                      #qt
        }
    def __init__(self):
        QtGui.QPushButton.__init__(self)                    #qt

    def set(self, on):
        self.setChecked(on)                                 #qt

    def active(self):
        return self.isChecked()                             #qt


class ComboBox(QtGui.QComboBox, WBase):                     #qt
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


class ListChoice(QtGui.QListWidget, WBase):                 #qt
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


class List(QtGui.QTreeWidget, WBase):                       #qt
    # Only using top-level items
    s_default = "select"
    s_signals = {
            "select": "itemSelectionChanged()" ,            #qt
        }
    def __init__(self):
        QtGui.QTreeWidget.__init__(self)                    #qt
        self.mode = ""
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) #qt
        self.setRootIsDecorated(False)                      #qt

    def x__selectionmode(self, sm):
        self.mode = sm
        if sm == "None":
            self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)  #qt
        elif sm == "Single":
            self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection) #qt
        else:
            self.mode = ""
            self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) #qt

    def setHeaders(self, headers):                          #qt
        self.setHeaderLabels(headers)                       #qt

    def set(self, items, index=0):                          #qt
        # Note that each item must be a tuple/list containing
        # entries for each column.
        self.clear()                                        #qt
        c = 0
        for i in items:
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


class LineEdit(QtGui.QLineEdit, WBase):                     #qt
    s_default = "changed"
    s_signals = {
            "enter": "returnPressed()",                     #qt
            "changed": "textEdited(const QString &)"        #qt
        }
    def __init__(self):
        QtGui.QLineEdit.__init__(self)                      #qt

    def get(self):
        return unicode(self.text())                         #qt

    def x__ro(self, ro):
        self.setReadOnly(ro)                                #qt


class CheckList(QtGui.QWidget, WBase):                      #qt
    def __init__(self):
        QtGui.QWidget.__init__(self)                        #qt
        self.box = QtGui.QVBoxLayout(self)                  #qt
        self.title = None
        if text:                                            #qt
            l.addWidget(QtGui.QLabel(text))                 #qt
        self.widget = QtGui.QListWidget()                   #qt
        l.addWidget(self.widget)                            #qt

    def x__title(self, text):
        if self.title:
            self.title.setText(text)                        #qt
        else:
            self.title = QtGui.QLabel(text)                 #qt
            self.box.insertWidget(0, self.title)            #qt

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


class TextEdit(QtGui.QTextEdit, WBase):                     #qt
    def __init__(self):
        QtGui.QTextEdit.__init__(self)                      #qt

    def x__ro(self, ro):
        self.setReadOnly(ro)                                #qt

    def append_and_scroll(self, text):
        self.append(text)                                   #qt
        self.ensureCursorVisible()                          #qt

    def get(self):
        return unicode(self.toPlainText())                  #qt

    def undo(self):
        QtGui.QTextEdit.undo(self)                          #qt


class HtmlView(QtGui.QTextBrowser, WBase):                  #qt
    def __init__(self):
        QtGui.QTextBrowser.__init__(self)                   #qt

    def x__html(self, content):
        self.setHtml(content)                               #qt


class SpinBox(QtGui.QDoubleSpinBox, WBase):                 #qt
    s_default = "changed"
    s_signals = {
            "changed": "valueChanged(double)"               #qt
        }
    def __init__(self):
        QtGui.QDoubleSpinBox.__init__(self)                 #qt
        self.step = None

    def x__min(self, min):
        self.setMinimum(min)

    def x__max(self, max):
        self.setMaximum(max)

    def x__decimals(self, dec):
        self.setDecimals(dec)
        if not self.step:
            self.setSingleStep(10**(-dec))

    def x__step(self, step):
        self.setSingleStep(step)

    def x__value(self, val):
        self.setValue(val)


class ProgressBar(QtGui.QProgressBar, WBase):               #qt
    def __init__(self):
        QtGui.QProgressBar.__init__(self)                   #qt

    def set(self, value):
        self.setValue(value)                                #qt

    def x__max(self, max):
        self.setMaximum(max)                                #qt



# Layout classes
class Layout:
    """A mixin base class for all layout widgets.
    """
    pass

boxmargin=3
class _BOX(Layout):
    def __init__(self, items):
        self.setContentsMargins(boxmargin, boxmargin, boxmargin, boxmargin) #qt
        for wl in items:
            if isinstance(wl, QtGui.QWidget):               #qt
                self.addWidget(wl)                          #qt
            elif isinstance(wl, SPACE):                     #qt
                if wl.size:                                 #qt
                    self.addSpacing(wl.size)                #qt
                self.addStretch()                           #qt
            elif isinstance(wl, Layout):                    #qt
                self.addLayout(wl)                          #qt
            else:                                           #qt
                gui_error("Invalid Box entry: %s" % repr(wl))


class VBOX(QtGui.QVBoxLayout, _BOX):                        #qt
    def __init__(self, *items):
        QtGui.QVBoxLayout.__init__(self)                    #qt
        _BOX.__init__(self, items)                          #qt


class HBOX(QtGui.QHBoxLayout, _BOX):                        #qt
    def __init__(self, *items):
        QtGui.QHBoxLayout.__init__(self)                    #qt
        _BOX.__init__(self, items)                          #qt


class GRID(QtGui.QGridLayout, Layout):                      #qt
    def __init__(self, *rows):
        QtGui.QGridLayout.__init__(self)                    #qt
        y = -1
        for row in rows:
            if not isinstance(row, GRIDROW):
                gui_error("Grid layouts must be built from 'GRIDROW's ('*+*')."
                        "\nFound:\n  %s" % repr(row))

            y += 1
            x = -1
            for wl in row.items:
                x += 1
                if isinstance(wl, Span):
                    continue
                # Determine the row and column spans
                x1 = x + 1
                while (x1 < len(row.items)) and isinstance(row.items[x1], CSPAN):
                    x1 += 1
                y1 = y + 1
                while (y1 < len(rows)) and isinstance(rows[y1].items[x], RSPAN):
                    y1 += 1

                if isinstance(wl, QtGui.QWidget):           #qt
                    self.addWidget(wl, y, x, y1-y, x1-x)    #qt
                elif isinstance(wl, Layout):
                    self.addLayout(wl, y, x, y1-y, x1-x)    #qt
                elif isinstance(wl, SPACE):
                    self.addItem(QtGui.QSpacerItem(wl.size, wl.height),
                            y, x, y1-y, x1-x)               #qt
                else:
                    gui_error("Invalid entry in Grid layout: %s" % repr(wl))


class GRIDROW:
    """It is necessary to have a layout class for a grid row because a list
    is always interpreted as being a layout item.
    """
    def __init__(self, *items):
        self.items = items


class SPACE:
    """Can be used in boxes and grids. In boxes only size is of interest,
    and it also means vertical size in the case of a vbox. In grids size
    is the width.
    """
    def __init__(self, size_width=0, height=0):             #qt
        self.size = size_width                              #qt
        self.height = height                                #qt


class Span:
    """Class to group special grid layout objects together - it doesn't
    actually do anything itself, but is used for checking object types.
    """
    pass


class CSPAN(Span):
    """Column-span layout item. It doesn't do anything itself, but it is used
    by the Grid layout constructor.
    """
    pass


class RSPAN(Span):
    """Row-span layout item. It doesn't do anything itself, but it is used
    by the Grid layout constructor.
    """
    pass


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
    def __init__(self, source, signal, name=None):
        """'source' is the widget object which initiates the signal.
        'signal' is the signal type.
        If 'name' is given, the signal will get this as its name,
        and this name may be used for more than one connection.
        Otherwise the name is built from the name of the source widget and
        the signal type as 'source*signal' and may only be used once.
        If 'name' begins with '+' an additional argument, the source
        widget name, will be inserted at the head of the argument list.
        """
        self.signame = signal
        self.tag = None
        sig = source.s_signals.get(signal)
        if not sig:
            gui_warning("Signal '%s' is not defined for '%s'."
                        % (signal, source.w_name))
            return
        if name:
            l = guiapp.connections.get(name, [])
            if name.startswith("+"):
                self.tag = source.w_name
        else:
            l = self
            name = "%s*%s" % (source.w_name, signal)
            if guiapp.connections.has_key(name):
                gui_warning("Signal '%s' is defined more than once." % name)
                return
        self.name = name
        try:
            self.convert = getattr(source, "s_%s" % signal)
        except:
            self.convert = None
        if QtCore.QObject.connect(source, QtCore.SIGNAL(sig), self.signal): #qt
            if l != self:
                l.append(self)
            guiapp.connections[name] = l
        else:
            gui_warning("Signal '%s' couldn't be connected." % name)

    def signal(self, *args):
        if self.convert:
            args = self.convert(*args)
        if self.tag:
            guiapp.sendsignal(self.name, self.tag, *args)
        else:
            guiapp.sendsignal(self.name, *args)

#    def disconnect(self):
#        ???


class GuiApp:
    """This class represents an application gui, possibly with more than
    one top level window, these being defined in layout files.
    """
    def __init__(self):
        global guiapp
        guiapp = self
        self.qtapp = QtGui.QApplication([])                 #qt

        self.connections = {}
        self.widgets = {}


    def addwidget(self, fullname, wo):
        if self.widgets.has_key(fullname):
            gui_error("Attempted to define widget '%s' twice." % fullname)
        self.widgets[fullname] = wo


    def getwidget(self, wname):
        if self.widgets.has_key(wname):
            return self.widgets[wname]
        gui_error("Unknown widget: '%s'" % wname)


    def show(self, windowname):
        self.getwidget(windowname).setVisible()


    def new_line(self, line):
        """An input line has been received.
        The initial character determines the action:
            '!' - method calls to an exported widget, with no result.
                They have the form '!widget.method [arg1, arg2, ...]'
                where the argument list is json-encoded. If there are no
                arguments the square brackets needn't be present.
            '?' - similar to '!', but a return value is expected. It has
                a key value, which is everything up to the first ':' After
                that the arguments are as for '!'. The result is '@' followed
                by the key value, then ':', then the json-encoded call result.
            '%' - widget definition. The form is
                '%widget-type widget-name {attributes}', where the attribute
                dict is optional. If widget-name starts with '^' this will be
                stripped and the default signal for this widget will be enabled.
            '$' - set a layout on an existing widget. The form is
                '$ widget-name layout', where layout is in list form (see below).
            '^' -  enable emission of the given signal. The form is
                '^widget-name signal-type signal-name' where signal-name is
                optional (see below for details).
        """
        line = str(line).rstrip()

        if line[0] == "!":
            # Process a method call - a command with no response
            try:
                self._methodcall(line[1:])
            except:
                onexcept("Bad gui command line:\n  " + line)

        elif line[0] == "?":
            # Process a method call - an enquiry.
            try:
                l, r = line.split(":", 1)
                res = self._methodcall(r)
            except:
                onexcept("Bad gui enquiry line:\n  " + line)
            self.send("@", "%s:%s" % (l[1:], json.dumps(res)))

        elif line[0] == "%":
            # Add a widget
            try:
                args = line[1:].split(None, 2)
                if len(args) > 2:
                    a = json.loads(args[2])
                    assert isinstance(a, dict)
                else:
                    a = {}
                self.newwidget(args[0], args[1], a)
            except:
                onexcept("Bad widget definition:\n  " + line)
                # fatal

        elif line[0] == "$":
            # Set a widget's layout
            try:
                wn, l = line[1:].split(None, 1)
                self.layout(wn, json.loads(l))
            except:
                onexcept("Bad layout line:\n  " + line)

        elif line[0] == "^":
            # Enable a signal
            args = line[1:].split()
            w = self.getwidget(args[0])
            if w:
                Signal(w, *args[1:])

        elif line[0] == "/":
            # Quit
            arg = line[1:].strip()
            self.send("/", arg if arg else "0")
            guiapp.qtapp.quit()

        else:
            self.got(line)

        ithread.event.set()


    def _methodcall(self, text):
        wma = text.split(None, 1)
        cmd = specials_table.get(wma[0])
        if not cmd:
            w, m = wma[0].split(".")
            wo = self.getwidget(w)
            cmd = getattr(wo, m)
        if len(wma) > 1:
            return cmd(*json.loads(wma[1]))
        else:
            return cmd()


    def got(self, line):
        """Reimplement this in a sub-class to do something else?
        """
        gui_error("Unexpected input line:\n  " + line)


    def send(self, mtype, line):
        """Reimplement this in a sub-class to do something else?
        """
        sys.stdout.write("%s%s\n" % (mtype, line))
        sys.stdout.flush()


    def sendsignal(self, name, *args):
        self.send("^", name + " " + json.dumps(args))


    def newwidget(self, wtype, wname, args):
        if wname[0] == "^":
            wname = wname[1:]
            connect = True
        else:
            connect = False

        wobj = widget_table[wtype]()
        wobj.w_name = wname

        # Attributes
        for key, val in args.iteritems():
            handler = "x__" + key
            if hasattr(wobj, handler):
                getattr(wobj, handler)(val)
# Unrecognized attributes are ignored ...

        # The widget may itself have created widgets that need including
        if hasattr(wobj, "x_mywidgets"):
            for n, w in wobj.x_mywidgets.iteritems():
                self.addwidget(n, w)
        if connect:
            Signal(wobj, wobj.s_default)
        self.addwidget(wname, wobj)


# A layout call specifies and organizes the contents of a widget. The first
# argument is the name of the widget, the second argument is a layout
# manager list.

# There are three sorts of thing which can appear in layout manager lists
# (apart from the layout type at the head of the list and an optional attribute
# dict as second item). There can be named widgets, there can be further layout
# managers (specified as lists, nested as deeply as you like) and there
# can be layout widgets, like spacers and separators.

# A layout widget can appear in two forms - either as a simple string (the
# layout widget type), or as a list with two entries, the layout widget type
# and an attribute dict. In the former case all attributes take on their
# default values.
    def layout(self, wname, ltree):
        wobj = self.getwidget(wname)
        assert isinstance(ltree, list)
        lobj = self.getobj(ltree)
        assert isinstance(lobj, Layout)
        wobj.setLayout(lobj)                                #qt


    def getobj(self, item):
        if isinstance(item, list):
            if (len(item) > 1) and isinstance(item[1], dict):
                dictarg = item[1]
                ilist = item[2:]
            else:
                dictarg = {}
                ilist = item[1:]
            if item[0].endswith("*"):
                args = [self.getobj(i) for i in ilist]
            else:
                args = ilist
            return self.newlayout(item[0], dictarg, args)

        elif item.startswith("*"):
            return self.newlayout(item, {}, [])

        else:
            return self.getwidget(item)


    def newlayout(self, item, parms, args):
        lfunc = layout_table.get(item)
        if lfunc:
            lobj = lfunc(*args)
            # Attributes
            for key, val in parms:
                handler = "x__" + key
                if hasattr(lobj, handler):
                    getattr(lobj, handler)(val)
            return lobj
        else:
            gui_error("Unknown layout type: %s" % item)


    def getwidget(self, w):
        widget = self.widgets.get(w)
        if not widget:
            gui_warning("Unknown widget: %s" % w)
        return widget


#+++++++++++++++++++++++++++
# Catch all unhandled errors.
def errorTrap(type, value, tb):
    etext = "".join(traceback.format_exception(type, value, tb))
    gui_error(etext, "This error could not be handled.")

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
    "SpinBox": SpinBox,
    "ProgressBar": ProgressBar,
}

specials_table = {
    "textLineDialog": textLineDialog,
    "infoDialog": infoDialog,
    "confirmDialog": confirmDialog,
    "errorDialog": gui_error,
    "warningDialog": gui_warning,
    "fileDialog": fileDialog,
}

layout_table = {
    "*VBOX*": VBOX,
    "*HBOX*": HBOX,
    "*GRID*": GRID,
    "*+*": GRIDROW,
    "*-": CSPAN,
    "*|": RSPAN,
    "*SPACE": SPACE,
    "*VLINE": VLINE,
    "*HLINE": HLINE,
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
        self.event = threading.Event()
        self.event.set()

    def run(self):
        while True:
            line = self.input.readline()
            if not line:        # Is this at all possible?
                return
            self.event.wait()
            self.event.clear()
            self.emit(self.lineReady, line)                 #qt
#---------------------------

if __name__ == "__main__":
    GuiApp()

    ithread = Input(sys.stdin, guiapp.new_line)
    ithread.start()

    guiapp.qtapp.exec_()                                    #qt

