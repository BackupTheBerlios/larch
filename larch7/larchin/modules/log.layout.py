# GUI description for larchin log window
# 2009.09.29

Namespace = "log:"

Widgets = [
["*Window", "log", "larchin log"],

# Header
["Label", "header", _("Here you can follow the progress of the commands.")],

# Main Widget
["*TextEdit", "logtext", "ro"],
["Button", "^log_clear", _("Clear")],
["Button", "^log_hide", _("Hide")],

]


################# Signals
Signals = [
#[<source-widget>, <signal>]
#    -> <namespace><source-widget>*<signal> [None, [<actual args>]]
#[<source-widget>, <signal>, <newname>]
#    -> <newname> [None, [<actual args>]]
#[<source-widget>, <signal>, <newname>, <tag>]
#    -> <newname> [<tag>, [<actual args>]]

]


################# Layout
Layout = [
# Main widget
["+MAIN", ["header", "logtext", "hb"]],

["HBOX", "hb", ["hs", "log_clear", "log_hide"]],
 ["HSPACE", "hs"],

]

# Attributes are supported on the understanding that they can be
# interpreted rather freely, and maybe not at all.
# One could also have separate (cascading?) files to adjust the
# entries here - it might help in adjusting to different front ends
# without having to change the base description.

Attributes = [
["log", "size", "600_400"],
]

StringFormats = {

}

