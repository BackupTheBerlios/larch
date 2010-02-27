#!/usr/bin/env python
#
# lardmgui.py   --  Qt-based GUI code for lardm
#
# (c) Copyright 2009, 2010 Michael Towers (larch42 at googlemail dot com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#-------------------------------------------------------------------
# 2010.02.27

from PyQt4 import QtGui, QtCore


class LardmGui(QtGui.QGraphicsView):
    def __init__(self):
        self.starting = True
        QtGui.QGraphicsView.__init__(self)
        self.width = 0
        self.height = 0
        self.bgimage = None
        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)

        # Need some way of setting the widget sizes and positions from
        # the event loop, as the necessary information is not available
        # before this starts.
        #self.connect(self.scene,
        #        QtCore.SIGNAL("changed ( const QList<QRectF>& )"),
        #        self.newSize)
        self.connect(app, QtCore.SIGNAL("focusChanged(QWidget*, QWidget*)"),
                self.newfocus)

        self.showFullScreen()

        img = theme["background_image"]
        if img:
            self.setbgImage(img)

        self.activateWindow()


    def makegui(self):
        if theme["showusers"]:
            ulw = self.scene.addWidget(self.userlistWidget())
            ulw.setGeometry(QtCore.QRectF(*theme["showusers_geometry"]))

        login_w = QtGui.QWidget()
        login__ = QtGui.QGridLayout()
        login_w.setLayout(login__)

        uw_l = QtGui.QLabel(_("Login name:"))
        self.username_w = QtGui.QLineEdit()
        self.connect(self.username_w, QtCore.SIGNAL("returnPressed()"),
                self.pwenter)
        # Add completer to user line edit
        completer = QtGui.QCompleter(self.userlist)
        completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)
        self.username_w.setCompleter(completer)

        pw_l = QtGui.QLabel(_("Password:"))
        self.password_w = PwLineEdit()
        self.connect(self.password_w, QtCore.SIGNAL("returnPressed()"),
                self.handle_login)
        self.password_w.setEchoMode(QtGui.QLineEdit.Password)
        login_w.setLayout(login__)

        login__.addWidget(uw_l, 0, 0)
        login__.addWidget(self.username_w, 0, 1)
        login__.addWidget(pw_l, 1, 0)
        login__.addWidget(self.password_w, 1, 1)

        loginw = self.scene.addWidget(login_w)
        loginw.setGeometry(QtCore.QRectF(*theme["login_geometry"]))

        buttons_w = QtGui.QWidget()
        buttons__ = QtGui.QHBoxLayout()
        buttons_w.setLayout(buttons__)

        self.done = QtGui.QPushButton(_("Login"))
        #done.setAutoDefault(True)
        self.connect(self.done, QtCore.SIGNAL("clicked()"), self.handle_login)
        restart = QtGui.QPushButton(_("Restart"))
        self.connect(restart, QtCore.SIGNAL("clicked()"), self.handle_restart)
        shutdown = QtGui.QPushButton(_("Shutdown"))
        self.connect(shutdown, QtCore.SIGNAL("clicked()"), self.handle_shutdown)

        buttons__.addWidget(shutdown)
        buttons__.addWidget(restart)
        buttons__.addStretch()
        buttons__.addWidget(self.done)

        buttonsw = self.scene.addWidget(buttons_w)
        buttonsw.setZValue(10)
        buttonsw.setGeometry(QtCore.QRectF(*theme["buttons_geometry"]))


    def newSize(self):
        vp = self.viewport()
        width = vp.width()
        height = vp.height()
        if self.width == width and self.height == height:
            return
        self.width = width
        self.height = height
        self.scene.setSceneRect(-width / 2.0, -height / 2.0, width, height)
        if self.bgimage:
            bgpm = self.bgimage.pixmap()
            w = bgpm.width()
            h = bgpm.height()
            sw = float(self.width)
            sh = float(self.height)

            if theme["image_scale"]:
                s = sw/w if sw/w >= sh/h else sh/h
            else:
                s = 1.0
            sx = s
            sy = s
            t = QtGui.QTransform(sx, 0, 0, sy, -sx*w/2, -sy*h/2)
            self.bgimage.setTransform(t)


    def setbgColour(self, colour):
        self.scene.setBackgroundBrush(QtGui.QColor(colour))


    def setbgImage(self, path):
        """Set an image as canvas background.
        """
        if self.bgimage:
            if not path:
                self.scene.removeItem(self.bgimage)
                self.bgimage = None
                return
        else:
            self.bgimage = QtGui.QGraphicsPixmapItem()
            self.bgimage.setZValue(-100)
            self.scene.addItem(self.bgimage)
        bgpm = QtGui.QPixmap(path)
        self.bgimage.setPixmap(bgpm)


    def pwenter(self):
        user = self.username_w.text()
        self.password_w.setText("")
        self.password_w.setFocus()


    def newfocus(self, old, new):
        if new == lardmgui:
            if self.starting:
                self.starting = False
                self.newSize()
                self.makegui()
            self.username_w.setFocus()


    def handle_login(self):
        u = unicode(self.username_w.text())
        p = unicode(self.password_w.text())
        em = self.login(u, p)
        if em:
            self.password_w.setText("")
            self.password_w.setFocus()
            QtGui.QMessageBox.warning(self.done, "", em)
        else:
            app.exit(0)


    def exitcheck(self, tty):
        if tty and (QtGui.QMessageBox.warning(self.done, "",
                _("At least one session is still open.\n Close it/them ?"),
                    QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
                    != QtGui.QMessageBox.Yes):
            self.switch_tty(tty)
        app.exit(0)


    def handle_restart(self):
        self.exitcheck(self.shutdown("restart"))


    def handle_shutdown(self):
        self.exitcheck(self.shutdown("shutdown"))


    def setUser(self, index):
        self.username_w.setText(self.userlist[index])
        self.username_w.setFocus()


    def userlistWidget(self):
        """Set up the list of 'normal' users, i.e. those with a home
        directory in /home and a login shell (ending with 'sh').
        """
        uw = ListWidget([_("USERS")], selectionmode="Single")
        uw.set([[i] for i in self.userlist], -1)
        uw.connect("select", self.setUser)
        return uw


########### Qt widgets ############

class PwLineEdit(QtGui.QLineEdit):
    def __init__(self):
        QtGui.QLineEdit.__init__(self)

    def focusInEvent(self, e):
        user = unicode(lardmgui.username_w.text())
        if user not in lardmgui.userlist:
            lardmgui.username_w.setFocus()
            return

        QtGui.QLineEdit.focusInEvent(self, e)


class ListWidget(QtGui.QTreeWidget):
    def __init__(self, headers, **kwargs):
        QtGui.QTreeWidget.__init__(self)
        self.setRootIsDecorated(False)

        self.mode = kwargs.get("selectionmode", "")
        if self.mode == "None":
            self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        elif self.mode == "Single":
            self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        else:
            self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.setHeaderLabels(headers)
        hi = self.headerItem()

    def connect(self, signal, slot):
        if signal == "select":
            self._selectslot = slot
            QtCore.QObject.connect(self,
                    QtCore.SIGNAL("itemSelectionChanged()"),
                    self.s_select)

    def s_select(self):
        # Signal a selection change, passing the new selection list (indexes)
        s = [self.indexOfTopLevelItem(i) for i in self.selectedItems()] #qt
        if self.mode == "Single":
            s = s[0]
        self._selectslot(s)

    def set(self, items, index=0):
        # Note that each item must be a tuple/list containing
        # entries for each column.
        self.clear()
        c = 0
        for i in items:
            item = QtGui.QTreeWidgetItem(self, i)
            self.addTopLevelItem(item)
            if c == index:
                self.setCurrentItem(item)
            c += 1



def init():
    global app
    app = QtGui.QApplication([])
    app.setStyleSheet(theme["stylesheet"])


def mainloop(gui):
    global lardmgui
    lardmgui = gui
    lardmgui.show()
    return app.exec_()
