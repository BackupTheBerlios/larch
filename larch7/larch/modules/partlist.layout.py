# GUI description for larch partition choice dialog
# 2009.08.12

Namespace = "parts:"

Widgets = [
["*Dialog",  "parts", _("Choose Partition"), "larchicon.png"],

["*Label", "label", _("BE CAREFUL - if you select the wrong\n"
        "   partition you might well destroy your system!"
        "\n\nSelect the partition to receive the larch system:")],
["*ListChoice", "list"],
["*LineEdit", "choice"],

#OK and Cancel pushbuttons, or Save and Discard - QDialogButtonBox?
["DialogButtons", "buttons", "Save", "Discard"],

#Undo and redo?

]

################# Signals
Signals = [
["+INTERNAL", "buttons"],
["list", "changed", "$parts:list*changed$"]
]


# Attributes are supported on the understanding that they can be
# interpreted rather freely, and maybe not at all.
# One could also have separate (cascading?) files to adjust the
# entries here - it might help in adjusting to different front ends
# without having to change the base description.

Attributes = [
#["parts", "size", "600_400"],
]

StringFormats = {

}

Layout = [
# Main widget
["+MAIN", ["label", "list", "choice", "buttons"]],
]
