#!/usr/bin/env python
import sys

try:
   import pygtk
   pygtk.require("2.6")
except:
   pass

try:
   import gtk, gobject
except:
   sys.exit(1)

class CellRendererExample:
   """ Main class of the application. """

   items = ("item 1",
            "item 2",
            "item 3",
            "item 4",
            "item 5")

   def __init__(self):
       # Create window and connect its destroy signal.
       window = gtk.Window()
       window.connect("destroy", gtk.main_quit)

       # Create and add a treeview widget to the window.
       self.treeview = gtk.TreeView()
       window.add(self.treeview)

       # Create a text column
       column0 = gtk.TreeViewColumn("Text",
                                     gtk.CellRendererText(),
                                     text=0)

       # Create a combobox column
       lsmodel = gtk.ListStore(str)

       for item in self.items:
           lsmodel.append([item])

       cellcombo = gtk.CellRendererCombo()

       cellcombo.set_property("text-column", 0)
       cellcombo.set_property("editable", True)
       cellcombo.set_property("has-entry", False)
       cellcombo.set_property("model", lsmodel)

       cellcombo.connect("edited", self.cellcombo_edited)

       column1 = gtk.TreeViewColumn("Combobox", cellcombo, text=1)

       self.treeview.append_column(column0)
       self.treeview.append_column(column1)

       # Create liststore.
       liststore = gtk.ListStore(str, str)

       # Append a couple of rows.
       liststore.append(["Some text", "Click here to select an item."])
       liststore.append(["More text", "Click here to select an item."])
       liststore.append(["More text", "Click here to select an item."])
       liststore.append(["More text", "Click here to select an item."])
       liststore.append(["More text", "Click here to select an item."])

       # Set model.
       self.treeview.set_model(liststore)

       window.show_all()

   def cellcombo_edited(self, cellrenderertext, path, new_text):
       treeviewmodel = self.treeview.get_model()
       iter = treeviewmodel.get_iter(path)
       treeviewmodel.set_value(iter, 1, new_text)

   def main(self):
       gtk.main()

if __name__ == "__main__":
   cre = CellRendererExample()
   cre.main()
