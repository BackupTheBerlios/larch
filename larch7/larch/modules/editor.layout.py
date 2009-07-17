# GUI description for larch log window
# 2009.06.29

#Maybe this is a bit too minimal, so that it would be worth supplying it
# as a special case, rather like the error dialogs.

Namespace = "editor:"

Widgets = [
["*Dialog",  "editor", _("Editor"), "larchicon.png"],

["*Label", "label"],
["*TextEdit", "text"],

#OK and Cancel pushbuttons, or Save and Discard - QDialogButtonBox?
["DialogButtons", "buttons", "Save", "Discard"],

#Undo and redo?

]

################# Signals
Signals = [
["+INTERNAL", "buttons"],
]


# Attributes are supported on the understanding that they can be
# interpreted rather freely, and maybe not at all.
# One could also have separate (cascading?) files to adjust the
# entries here - it might help in adjusting to different front ends
# without having to change the base description.

Attributes = [

]

StringFormats = {

}

Layout = [
# Main widget
["+MAIN", ["label", "text", "buttons"]],
]
