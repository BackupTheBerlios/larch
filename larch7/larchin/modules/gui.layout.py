# GUI description for larchin main window
# 2009.10.03

Namespace = ":"

# Formatting strings
_imagefmt = '<img src="$" />'
_h2fmt = '<span style="font-size:24px; color:#c55500;"><strong>$</strong></span>'
_h1fmt = _h2fmt.replace("$", "<em>$</em>")
_stagehfmt = '<span style="font-size:18px; color:#55c500;">$</span>'

Widgets = [
["*Window", "larchin", "larchin", "larchin-icon.png"],

# Header
["Label", "image", "larchin80.png", _imagefmt],

["Label", "header1", "larch", _h1fmt],
["Label", "header2", _("Installer"), _h2fmt],

["*ToggleButton", "^showlog", _("View Log")],
["*ToggleButton", "^docs", _("Help")],
["*Button", "^cancel", _("Cancel")],
["Button", "^quit", _("Quit")],

["*Label", "stageheader", "", _stagehfmt],

# Main widget
["*Stack", "stack", [
        "page_welcome",
        "page_disks",
        "page_autopart",]
    ],

# Footer
["Button", "^forward", _("OK")],


# Welcome page ("page_welcome")
["Label", "wel1", _("Welcome to larchin, the easy way"
        " to install a ready-configured Arch Linux")],

["Label", "wel2", _("With this program you can install a larch"
        " live system as a normal Arch Linux system, retaining"
        " its configuration settings.")],

["Label", "wel3", _("Press the 'OK' button to progress to the next stage.")],


# Device selection page ("page_disks")
["*List", "^disks-device-list", "Single"],
["*List", "disks-device-partitions", "None"],

["*Button", "^ntfs-shrink", _("Shrink first partition (Windows - NTFS)")],

["Frame", "choose_partition_method", _("Choose Partitioning Method")],
  ["*RadioButton", "^auto", _("Autopartition and install to selected device")],
    ["*CheckBox", "^keep1", _("Keep first partition (Windows - NTFS)")],

  ["*RadioButton", "^guipart", _("Graphical partition manager")],
  ["*RadioButton", "^cfdisk", _("Console partition manager (cfdisk) on selected device")],
  ["*RadioButton", "^nopart", _("Use existing partitions")],


# Auto-partition page ("page_autopart")
["Label", "autopart_disk_l", _("Device:")],
["*LineEdit", "autopart_disk"],
["Label", "autopart_disksize_l", _("Total device capacity:")],
["*LineEdit", "autopart_disksize"],
["Label", "autopart_reserved_l", _("Reserved space:")],
["*LineEdit", "autopart_reserved"],

["*OptionalFrame", "^autoswap", _("Create Swap Partition")],



["*OptionalFrame", "^autohome", _("Create Separate Partition for User Data")],


["Label", "autopart_syssize_l", _("Space for Arch Root Partition:")],
["*LineEdit", "autopart_syssize"],


]
################# Tooltips
Tooltips = [
["cancel", _("Stop the current action")],
["quit", _("Stop current action and quit the program")],
["showlog", _("This button toggles the visibility of the log viewer")],
["docs", _("Open the larchin docs in a browser")],
["disks-device-list", _("Select the device to inspect, or for partitioning")],
["disks-device-partitions", _("The partitions on the selected device")],
["forward", _("Execute any operations pending on this page and continue to next")],
["autopart_reserved", _("Space not available because a Windows partition is to be saved")],

]


################# Signals
Signals = [

]


################# Layout
Layout = [
# Main widget
["+MAIN", ["hbh", "stack", "hbf"]],

["HBOX", "hbh", ["image", "vbh"]],
  ["VBOX", "vbh", ["hbh1", "hbh2"]],
    ["HBOX", "hbh1", ["header1", "header2", "hsh1", "showlog", "docs", "cancel", "quit"]],
      ["HSPACE", "hsh1"],
    ["HBOX", "hbh2", ["stageheader"]],
      #["HSPACE", "hsh2"],

["HBOX", "hbf", ["hsf", "forward"]],
  ["HSPACE", "hsf"],

# Welcome page ("page_welcome")
["+LAYOUT", "page_welcome", "vb_welcome"],
["VBOX", "vb_welcome", ["wel1", "wel2", "wel3"]],

# Device selection page ("page_disks")
["+LAYOUT", "page_disks", "vb_disks"],
["VBOX", "vb_disks", ["hb_disks1", "vs_disks", "choose_partition_method"]],
  ["HBOX", "hb_disks1", ["disks-device-list", "disks-device-partitions"]],
  ["VSPACE", "vs_disks"],

["+LAYOUT", "choose_partition_method", "hb_disks2"],
["HBOX", "hb_disks2", ["vb_disks_method", "hs_disks", "vb_disks_part1"]],
  ["HSPACE", "hs_disks", 50],
  ["VBOX", "vb_disks_method", ["auto", "guipart", "cfdisk", "nopart"]],
  ["VBOX", "vb_disks_part1", ["keep1", "ntfs-shrink", "vs_disks2"]],
    ["VSPACE", "vs_disks2"],

# Auto-partition page ("page_autopart")
["+LAYOUT", "page_autopart", "vb_autopart"],
["VBOX", "vb_autopart", ["hb_autopart1", "hb_autopart2", ]],
  ["HBOX", "hb_autopart1", ["autopart_disk_l", "autopart_disk", "hs_autopart1",
        "autopart_disksize_l", "autopart_disksize"]],
    ["HSPACE", "hs_autopart1"],

  ["HBOX", "hb_autopart2", ["autopart_reserved_l", "autopart_reserved"]],

#["*OptionalFrame", "^autoswap", _("Create Swap Partition")],



#["*OptionalFrame", "^autohome", _("Create Separate Partition for User Data")],


#["Label", "autopart_syssize_l", _("Space for Arch Root Partition:")],
#["*LineEdit", "autopart_syssize"],
]


# Attributes are supported on the understanding that they can be
# interpreted rather freely, and maybe not at all.
# One could also have separate (cascading?) files to adjust the
# entries here - it might help in adjusting to different front ends
# without having to change the base description.

Attributes = [
["stageheader", "align", "center"],
["autopart_disk", "readonly", "true"],
["autopart_disksize", "readonly", "true"],
["autopart_reserved", "readonly", "true"],
["autopart_syssize", "readonly", "true"],
]


