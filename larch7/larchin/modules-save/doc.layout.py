# GUI description for larchin help window
# 2009.10.02

Namespace = "doc:"

Widgets = [
["*Window", "help", _("larchin Help")],

# Main Widget
["*HtmlView", "content"],
["Button", "^hide", _("Hide")],

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
["+MAIN", ["content", "hb"]],

["HBOX", "hb", ["hs", "hide"]],
 ["HSPACE", "hs"],

]

# Attributes are supported on the understanding that they can be
# interpreted rather freely, and maybe not at all.
# One could also have separate (cascading?) files to adjust the
# entries here - it might help in adjusting to different front ends
# without having to change the base description.

Attributes = [
["help", "size", "600_400"],
]

StringFormats = {

}

