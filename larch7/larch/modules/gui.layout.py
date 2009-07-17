# GUI description for larch main window
# 2009.06.25

Namespace = ":"

Widgets = [
["*Window", "larch", "larch", "larchicon.png"],

# Header
["Label", "image", ["%1", ("larch80.png", "imageformat")]],

["Label", "header", ["%1 %2", ("larch", "larchformat"),
        (_("Live Arch Linux Construction Kit"), "titleformat")]],

["*ToggleButton", "^showlog", _("View Log")],


# Main widget
["*Notebook", "^notebook", [
            ("page_settings", _("Project Settings")),
            ("page_installation", _("Installation")),
            ("page_larchify", _("Larchify")),
            ("page_medium", _("Prepare Medium")),
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
  ["Button", "^pacmanconf", _("Edit pacman.conf template")],

["Frame", "pacman_sources", _("Pacman Sources")],
  ["Label", "larch_repo", _("larch Repository:")],
  ["*LineEdit", "larch_repo_show"],
  ["Button", "^larch_repo_change", _("Change")],
  ["Label", "mirror", _("Arch Mirror:")],
  ["*LineEdit", "mirror_show"],
  ["Button", "^mirror_change", _("Change")],

["OptionalFrame", "settings_advanced", _("Advanced Options")],
  ["*CheckList", "host_db", _("Synchronize to host db")],

  ["Label", "cache", _("Package Cache:")],
  ["*LineEdit", "cache_show"],
  ["Button", "^cache_change", _("Change")],
  ["Label", "db", _("Package db Source:")],
  ["*LineEdit", "db_show"],
  ["Button", "^db_change", _("Change")],

  ["Button", "^sync", _("Synchronize db")],
  ["Button", "^update", _("Update / Add package    [-U]")],
  ["Button", "^add", _("Add package(s)    [-S]")],
  ["Button", "^remove", _("Add package(s)    [-S]")],

["Button", "^install", _("Install")],


# Larchify Page
#TODO


# Prepare Medium Page
#TODO

]


################# Signals
Signals = [

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
["+LAYOUT", "page_settings", "vb2"],
["VBOX", "vb2", ["settings_profile", "vs1", "options_advanced"]],
 ["VSPACE", "vs1"],

["+LAYOUT", "settings_profile", "g1"],
["GRID", "g1",
    ["choose_profile", "choose_profile_combo", "vl1", "profile_rename"],
    ["new_profile",    "profile_browse",       "|",   "profile_delete"]
    ],
 ["VLINE", "vl1"],

["HBOX", "hb0", ["installation_path", "installation_path_show",
        "installation_path_change"]],

["+LAYOUT", "options_advanced", "vb3"],
["VBOX", "vb3", ["project", "hb0"]],
["+LAYOUT", "project", "hb1"],
["HBOX", "hb1", ["choose_project", "choose_project_combo", "new_project", "project_delete"]],

# Installation Page
["+LAYOUT", "page_installation", "vb4"],
["VBOX", "vb4", ["edit_profile", "pacman_sources", "settings_advanced",
        "hl1", "hb4"]],
 ["HLINE", "hl1"],

["+LAYOUT", "edit_profile", "hb2"],
["HBOX", "hb2", ["addedpacks", "baseveto", "pacmanconf"]],

["+LAYOUT", "pacman_sources", "g2"],
["GRID", "g2",
        ["larch_repo", "larch_repo_show", "larch_repo_change"],
        ["mirror",     "mirror_show",     "mirror_change"]
    ],

["+LAYOUT", "settings_advanced", "hb3"],
["HBOX", "hb3", ["host_db", "vl2", "vb5"]],
 ["VLINE", "vl2"],

["HBOX", "hb4", ["hs1", "install"]],
 ["HSPACE", "hs1"],
  # hb3 contents
  ["VBOX", "vb5", ["g3", "hl2", "g4"]],
   ["HLINE", "hl2"],

    ["GRID", "g3",
        ["cache", "cache_show", "cache_change"],
        ["db",    "db_show",    "db_change"]
    ],

    ["GRID", "g4",
        ["sync", "update"],
        ["add",  "remove"]
    ],

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
["larch_repo_show", "readonly", "true"],
["mirror_show", "readonly", "true"],
]

StringFormats = {
    "larchformat": ('<span style="font-size:24px; color:#c55500;">'
            '<strong><em>%s</em></strong>'),
    "titleformat": '<strong>%s</strong></span>',
    "imageformat": '<img src="%s" />'
}

