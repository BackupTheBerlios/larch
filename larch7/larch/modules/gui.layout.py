# GUI description for larch main window
# 2009.08.22

Namespace = ":"

Widgets = [
["*Window", "larch", "larch", "larchicon.png"],

# Header
["Label", "image", ["%1", ("larch80.png", "imageformat")]],

["Label", "header", ["%1 %2", ("larch", "larchformat"),
        (_("Live Arch Linux Construction Kit"), "titleformat")]],

["*ToggleButton", "showlog", _("View Log")],


# Main widget
["*Notebook", "^notebook", [
            ("page_settings", _("Project Settings")),
            ("page_installation", _("Installation")),
            ("page_larchify", _("Larchify")),
            ("page_medium", _("Prepare Medium")),
            ("page_tweaks", _("Installation Tweaks")),
        ]
    ],


# Project Settings Page
["Frame", "settings_profile", _("Profile")],
  ["Label", "choose_profile", _("Choose Existing Profile:")],
  ["Label", "new_profile", _("New Profile:")],
  ["*ComboBox", "^choose_profile_combo"],
  ["Button", "^profile_browse", _("Browse for Profile")],
  ["Button", "^profile_rename", _("Rename")],
  ["Button", "^profile_delete", _("Delete")],

["Label", "lplat", _("Platform (processor architecture):")],
["*ComboBox", "^platform"],

["OptionalFrame", "options_advanced", _("Advanced Options")],
  ["Frame", "project", _("Project")],
  ["Label", "choose_project", _("Choose Existing Project:")],
  ["*ComboBox", "^choose_project_combo"],
  ["Button", "^new_project", _("New Project")],
  ["Button", "^project_delete", _("Delete")],

  ["Label", "installation_path", _("Installation Path:")],
  ["*LineEdit", "installation_path_show"],
  ["Button", "^installation_path_change", _("Change")],


# Installation Page
["Frame", "edit_profile", _("Edit Profile")],
  ["Button", "^addedpacks", _("Edit 'addedpacks'")],
  ["Button", "^baseveto", _("Edit 'baseveto'")],
  ["Button", "^pacmanconf", _("Edit pacman.conf options")],
  ["Button", "^repos", _("Edit pacman.conf repositories")],

["OptionalFrame", "settings_advanced", _("Advanced Options")],
  ["*OptionalFrame", "^mirrorlist", _("Use project mirrorlist")],
  ["Button", "^mirrorlist_change", _("Edit project mirrorlist")],

  ["*OptionalFrame", "^use_local_mirror", _("Use local mirror for installation")],
    ["Label", "l1", _("URL:")],
    ["*LineEdit", "local_mirror"],
    ["Button", "^local_mirror_change", _("Change")],

  ["Label", "cache", _("Package Cache:")],
  ["*LineEdit", "cache_show"],
  ["Button", "^cache_change", _("Change")],

["Button", "^install", _("Install")],


# Installation Tweaks Page
["Frame", "pacmanops", _("Package Management")],
  ["Button", "^sync", _("Synchronize db")],
  ["Button", "^update", _("Update / Add package    [-U]")],
  ["Button", "^add", _("Add package(s)    [-S]")],
  ["Button", "^remove", _("Remove package(s)    [-Rs]")],


# Larchify Page
["Label", "larchify", _("The system to be compressed must be installed and ready.")],
["Button", "^locales", _("Edit supported locales")],
["Button", "^rcconf", _("Edit Arch configuration file (/etc/rc.conf)")],

["OptionalFrame", "larchify_advanced", _("Advanced Options")],
  ["Button", "^initcpio", _("Edit mkinitcpio.conf")],
  ["Button", "^overlay", _("Edit overlay (open in file browser)")],
  ["Button", "^filebrowser", _("(Configure file browser command)")],
  ["*CheckBox", "^ssh", _("Generate ssh keys")],
  ["*CheckBox", "oldsquash", _("Reuse existing system.sqf")],

["Button", "^build", _("Larchify")],


# Prepare Medium Page
#   - note that most of the RadioButtons need $names so that they are not blocked
["*Notebook", "^mediumtype", [
            ("medium_iso", "iso (CD/DVD)"),
            ("medium_partition", _("Partition (disk / USB-stick)")),
        ]
    ],

["Label", "lmiso", _("There are no options specific to iso media.")],

["Label", "lm2", _("Partition:")],
["*LineEdit", "larchpart"],
["Button", "^selectpart", _("Choose")],
["*CheckBox", "noformat", _("Don't format")],

["*Frame", "detection", _("Medium Detection")],
  ["*RadioButton", "^$uuid", "UUID"],
  ["*RadioButton", "^$label", "LABEL"],
  ["*RadioButton", "^$device", _("Partition")],
  ["*RadioButton", "^$nodevice", "Search (for larchboot)"],

  ["Label", "lm1", _("Medium label:")],
  ["*LineEdit", "labelname"],
  ["Button", "^changelabel", _("Change")],

["Frame", "bootloader", _("Bootloader")],
  ["*RadioButton", "^$grub", "GRUB"],
  ["*RadioButton", "^$syslinux", "syslinux/isolinux"],
  ["*RadioButton", "^$none", _("None")],
  ["Label", "lmb1", _("(You'll need to\nprovide some\nmeans of\nbooting)")],

["*CheckBox", "larchboot", _("Bootable using larchboot search")],

["Button", "^bootlines", _("Edit boot entries")],
["Button", "^grubtemplate", _("Edit grub template")],
["Button", "^syslinuxtemplate", _("Edit syslinux/isolinux template")],

["*Button", "^bootcd", _("Create boot iso")],
["Button", "^make", _("Create larch medium")],

]


################# Signals
Signals = [

["showlog", "toggled", "$showlog*toggled$"],

]


################# Layout
Layout = [
# Main widget
["+MAIN", ["hbh", "notebook"]],

["HBOX", "hbh", ["image", "vbh"]],
  ["VBOX", "vbh", ["hbh1", "hbh2"]],
    ["HBOX", "hbh1", ["header", "hsh1"]],
     ["HSPACE", "hsh1"],
    ["HBOX", "hbh2", ["hsh2", "showlog"]],
     ["HSPACE", "hsh2"],


# Project Settings Page
["+LAYOUT", "page_settings", "vb_ps"],
["VBOX", "vb_ps", ["settings_profile", "vs1", "hbplat", "options_advanced"]],
 ["VSPACE", "vs1"],

["+LAYOUT", "settings_profile", "g1"],
["GRID", "g1",
    ["choose_profile", "choose_profile_combo", "vl1", "profile_rename"],
    ["new_profile",    "profile_browse",       "|",   "profile_delete"]
    ],
 ["VLINE", "vl1"],

["HBOX", "hbplat", ["hsplat", "lplat", "platform"]],
  ["HSPACE", "hsplat"],

["HBOX", "hb0", ["installation_path", "installation_path_show",
        "installation_path_change"]],

["+LAYOUT", "options_advanced", "vb3"],
["VBOX", "vb3", ["project", "hb0"]],
["+LAYOUT", "project", "hb1"],
["HBOX", "hb1", ["choose_project", "choose_project_combo", "new_project", "project_delete"]],


# Installation Page
["+LAYOUT", "page_installation", "vb_pi"],
["VBOX", "vb_pi", ["edit_profile", "settings_advanced", "hl1", "hb4"]],
 ["HLINE", "hl1"],

["+LAYOUT", "edit_profile", "g2"],
["GRID", "g2",
        ["addedpacks", "baseveto"],
        ["pacmanconf", "repos"]
    ],

["+LAYOUT", "settings_advanced", "vb5"],
["VBOX", "vb5", ["hbi1", "hb5"]],
  ["HBOX", "hbi1", ["mirrorlist", "use_local_mirror"]],
  ["HBOX", "hb5", ["cache", "cache_show", "cache_change"]],

["+LAYOUT", "mirrorlist", "hb2"],
["HBOX", "hb2", ["mirrorlist_change"]],

["+LAYOUT", "use_local_mirror", "hb6"],
["HBOX", "hb6", ["l1", "local_mirror", "local_mirror_change"]],

["HBOX", "hb4", ["hs1", "install"]],
 ["HSPACE", "hs1"],


# Installation Tweaks Page
["+LAYOUT", "page_tweaks", "vb_pt"],
["VBOX", "vb_pt", ["g3", "vst1"]],
  ["GRID", "g3",
        ["sync", "update"],
        ["add", "remove"]
    ],
  ["VSPACE", "vst1"],


# Larchify Page
["+LAYOUT", "page_larchify", "vb_pl"],
["VBOX", "vb_pl", ["larchify", "vbs1", "hbl2",
        "vbs2", "larchify_advanced", "hbl1"]],
  ["HBOX", "hbl2", ["locales", "hsl3", "rcconf"]],
    ["HSPACE", "hsl3"],
  ["VSPACE", "vbs1"],
  ["VSPACE", "vbs2"],

  ["+LAYOUT", "larchify_advanced", "hbl3"],
  ["HBOX", "hbl3", ["vbl1", "hsl2", "vbl2"]],
    ["VBOX", "vbl1", ["initcpio", "overlay", "filebrowser"]],
    ["VBOX", "vbl2", ["ssh", "vsl1", "oldsquash"]],
      ["VSPACE", "vsl1"],
   ["HSPACE", "hsl2"],

["HBOX", "hbl1", ["hsl1", "build"]],
 ["HSPACE", "hsl1"],


# Prepare Medium Page
["+LAYOUT", "page_medium", "vb_pm"],
["VBOX", "vb_pm", ["hb_pm", "hbm3", "hlm1", "hbm4"]],
  ["HBOX", "hb_pm", ["vbm4", "bootloader"]],
    ["VBOX", "vbm4", ["mediumtype", "vsm1"]],
    ["VSPACE", "vsm1"],
  ["HLINE", "hlm1"],

["+LAYOUT", "medium_iso", "vbm1"],
["VBOX", "vbm1", ["vsmi2", "lmiso", "vsmi2"]],
  ["VSPACE", "vsmi1"],
  ["VSPACE", "vsmi2"],

["+LAYOUT", "medium_partition", "vbm2"],
["VBOX", "vbm2", ["hbm1", "detection", "hbm5"]],
  ["HBOX", "hbm1", ["lm2", "larchpart", "selectpart", "noformat"]],
  ["HBOX", "hbm5", ["bootcd", "vlm1", "larchboot"]],
    ["VLINE", "vlm1"],

  ["+LAYOUT", "detection", "vbm3"],
  ["VBOX", "vbm3", ["hbm2a", "hbm2b"]],
    ["HBOX", "hbm2a", ["$device", "$uuid", "$label", "$nodevice"]],
    ["HBOX", "hbm2b", ["lm1", "labelname", "changelabel"]],


["+LAYOUT", "bootloader", "vbm21"],
["VBOX", "vbm21", ["$grub", "$syslinux", "vsmb1", "hlmb1", "vsmb2", "$none", "lmb1"]],
  ["HLINE", "hlmb1"],
  ["VSPACE", "vsmb1"],
  ["VSPACE", "vsmb2"],

["HBOX", "hbm3", ["bootlines", "grubtemplate", "syslinuxtemplate"]],

["HBOX", "hbm4", ["hsm1", "make"]],
  ["HSPACE", "hsm1"],

]


# Attributes are supported on the understanding that they can be
# interpreted rather freely, and maybe not at all.
# One could also have separate (cascading?) files to adjust the
# entries here - it might help in adjusting to different front ends
# without having to change the base description.

Attributes = [
["choose_profile", "align", "right"],
["new_profile", "align", "right"],
["installation_path_show", "readonly", "true"],
["local_mirror", "readonly", "true"],
["larchpart", "readonly", "true"],
["labelname", "readonly", "true"],
]

StringFormats = {
    "larchformat": ('<span style="font-size:24px; color:#c55500;">'
            '<strong><em>%s</em></strong>'),
    "titleformat": '<strong>%s</strong></span>',
    "imageformat": '<img src="%s" />'
}

