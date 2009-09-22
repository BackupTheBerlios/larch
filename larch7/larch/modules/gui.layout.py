# GUI description for larch main window
# 2009.09.21

Namespace = ":"

Widgets = [
["*Window", "larch", "larch", "larchicon.png"],

# Header
["Label", "image", ["%1", ("larch80.png", "imageformat")]],

["Label", "header", ["%1 %2", ("larch", "larchformat"),
        (_("Live Arch Linux Construction Kit"), "titleformat")]],

["*ToggleButton", "showlog", _("View Log")],
["Button", "^docs", _("Help")],
["*Button", "^cancel", _("Cancel")],
["Button", "^quit", _("Quit")],


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
  ["Button", "^&profile_browse", _("Browse for Profile")],
  ["Button", "^&profile_rename", _("Rename")],
  ["Button", "^&profile_delete", _("Delete")],

["Label", "lplat", _("Platform (processor architecture):")],
["*ComboBox", "^platform"],

["OptionalFrame", "options_advanced", _("Advanced Options")],
  ["Frame", "project", _("Project")],
  ["Label", "choose_project", _("Choose Existing Project:")],
  ["*ComboBox", "^choose_project_combo"],
  ["Button", "^&new_project", _("New Project")],
  ["Button", "^&project_delete", _("Delete")],

  ["Label", "installation_path", _("Installation Path:")],
  ["*LineEdit", "installation_path_show"],
  ["Button", "^&installation_path_change", _("Change")],


# Installation Page
["Frame", "edit_profile", _("Edit Profile")],
  ["Button", "^&addedpacks", _("Edit 'addedpacks'")],
  ["Button", "^&baseveto", _("Edit 'baseveto'")],
  ["Button", "^&pacmanconf", _("Edit pacman.conf options")],
  ["Button", "^&repos", _("Edit pacman.conf repositories")],

["OptionalFrame", "settings_advanced", _("Advanced Options")],
  ["*OptionalFrame", "^mirrorlist", _("Use project mirrorlist")],
  ["Button", "^&mirrorlist_change", _("Edit project mirrorlist")],

  ["*OptionalFrame", "^use_local_mirror", _("Use special mirror for installation")],
    ["Label", "l1", _("URL:")],
    ["*LineEdit", "local_mirror"],
    ["Button", "^&local_mirror_change", _("Change")],

  ["Label", "cache", _("Package Cache:")],
  ["*LineEdit", "cache_show"],
  ["Button", "^&cache_change", _("Change")],

["Button", "^&install", _("Install")],


# Installation Tweaks Page
["*Frame", "pacmanops", _("Package Management")],
  ["Button", "^&sync", _("Synchronize db")],
  ["Button", "^&update", _("Update / Add package    [-U]")],
  ["Button", "^&add", _("Add package(s)    [-S]")],
  ["Button", "^&remove", _("Remove package(s)    [-Rs]")],

["*CheckBox", "^dlprogress", _("Show download progress (in log) - needs 'curl'")],

# Larchify Page
["Label", "larchify", _("The system to be compressed must be installed and ready.")],
["Button", "^&locales", _("Edit supported locales")],
["Button", "^&rcconf", _("Edit Arch configuration file (/etc/rc.conf)")],

["*OptionalFrame", "larchify_advanced", _("Advanced Options")],
  ["Button", "^&initcpio", _("Edit mkinitcpio.conf")],
  ["Button", "^overlay", _("Edit overlay (open in file browser)")],
  ["*CheckBox", "^ssh", _("Generate ssh keys")],
  ["*CheckBox", "oldsquash", _("Reuse existing system.sqf")],

["Button", "^&build", _("Larchify")],


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
["Button", "^&selectpart", _("Choose")],
["*CheckBox", "noformat", _("Don't format")],

["*Frame", "detection", _("Medium Detection")],
  ["*RadioButton", "^$uuid", "UUID"],
  ["*RadioButton", "^$label", "LABEL"],
  ["*RadioButton", "^$device", _("Partition")],
  ["*RadioButton", "^$search", "Search (for larchboot)"],

  ["Label", "lm1", _("Medium label:")],
  ["*LineEdit", "labelname"],
  ["Button", "^&changelabel", _("Change")],

["Frame", "bootloader", _("Bootloader")],
  ["*RadioButton", "^$grub", "GRUB"],
  ["*RadioButton", "^$syslinux", "syslinux/isolinux"],
  ["*RadioButton", "^$none", _("None")],
  ["Label", "lmb1", _("(You'll need to\nprovide some\nmeans of\nbooting)")],

["*CheckBox", "larchboot", _("Bootable using larchboot search")],

["Button", "^&bootlines", _("Edit boot entries")],
["Button", "^&grubtemplate", _("Edit grub template")],
["Button", "^&syslinuxtemplate", _("Edit syslinux/isolinux template")],

["*Button", "^&bootcd", _("Create boot iso")],
["Button", "^&make", _("Create larch medium")],

]


################# Tooltips
Tooltips = [
["cancel", _("Stop the current action")],
["quit", _("Stop current action and quit the program")],
["showlog", _("This button toggles the visibility of the log viewer")],
["docs", _("Open the larch docs in a browser")],
["choose_profile_combo", _("Choose a profile from those already in your larch working folder")],
["&profile_browse", _("Fetch a profile from the file-system")],
["&profile_rename", _("Rename the current profile")],
["&profile_delete", _("Delete the current profile")],
["platform", _("Which processor architecture?")],
["choose_project_combo", _("Choose a project from those already defined")],
["&new_project", _("Create a new project")],
["&project_delete", _("Delete the current project")],
["installation_path_show", _("The root directory of the Arch installation to larchify")],
["&installation_path_change", _("Change the root directory of the Arch installation")],
["&addedpacks", _("Edit the list of packages to be installed")],
["&baseveto", _("Edit the list of base packages NOT to install")],
["&pacmanconf", _("Edit pacman.conf options - not the repositories")],
["&repos", _("Edit the repository entries for pacman.conf")],
["mirrorlist", _("Enables use of the mirrorlist file saved in the working directory, for installation only")],
["&mirrorlist_change", _("Edit mirrorlist in working directory")],
["use_local_mirror", _("Allows a specific (e.g. local) mirror to be used just for the installation")],
["local_mirror", _("The url of the installation mirror")],
["&local_mirror_change", _("Change the installation mirror path")],
["cache_show", _("The path to the (host's) package cache")],
["&cache_change", _("Change the package cache path")],
["&install", _("This will start the installation to the set path")],
["&sync", _("Synchronize the pacman db on the target (pacman -Sy)")],
["&update", _("Update / Add a package from a package file using pacman -U")],
["&add", _("Add one or more packages (space separated) using pacman -S")],
["&remove", _("Remove one or more packages (space separated) using pacman -Rs")],
["dlprogress", _("Checking here should allow the log to display download progress by using a special download script")],
["&locales", _("Edit the /etc/locale.gen file to select supported glibc locales")],
["&rcconf", _("Edit the /etc/rc.conf file to configure the live system")],
["&initcpio", _("Edit the configuration file for generating the initramfs via mkinitcpio")],
["overlay", _("Open a file browser on the profile's 'rootoverlay'")],
["ssh", _("Enables pre-generation of ssh keys")],
["oldsquash", _("Reuse existing system.sqf, to save time if the base system hasn't changed")],
["&build", _("Build the main components of the larch system")],
["mediumtype", _("You can choose installation to iso (for CD/DVD) or a partition (e.g. USB-stick)")],
["larchpart", _("The partition to which the larch system is to be installed")],
["&selectpart", _("Select the partition to receive the larch system")],
["noformat", _("Copy the data to the partition without formatting first (not the normal procedure)")],
["detection", _("Choose how the boot scripts determine where to look for the larch system")],
["$uuid", _("Use the partition's UUID to find it")],
["$label", _("Use the partition's label to find it")],
["$device", _("Use the partition name (/dev/sdb1, etc.)")],
["$search", _("Test all CD/DVD devices and partitions until the file larch/larchboot is found")],
["labelname", _("The label that the partition will be given")],
["&changelabel", _("Change the label")],
["bootloader", _("You can choose between GRUB and syslinux/isolinux as bootloader")],
["$grub", _("Use GRUB as bootloader")],
["$syslinux", _("Use syslinux (partition) or isolinux (CD/DVD) as bootloader")],
["$none", _("Don't install a bootloader")],
["larchboot", _("Create the file larch/larchboot")],
["&bootlines", _("Edit the file determining the boot entries")],
["&grubtemplate", _("Edit grub template")],
["&syslinuxtemplate", _("Edit syslinux/isolinux template")],
["&bootcd", _("Create a small boot iso for this system (for machines that can't boot from USB)")],
["&make", _("Create the larch iso or set up the chosen partition")],

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
    ["HBOX", "hbh2", ["showlog", "docs", "hsh2", "cancel", "quit"]],
     ["HSPACE", "hsh2"],


# Project Settings Page
["+LAYOUT", "page_settings", "vb_ps"],
["VBOX", "vb_ps", ["settings_profile", "vs1", "hbplat", "options_advanced"]],
 ["VSPACE", "vs1"],

["+LAYOUT", "settings_profile", "g1"],
["GRID", "g1",
    ["choose_profile", "choose_profile_combo", "vl1", "&profile_rename"],
    ["new_profile",    "&profile_browse",       "|",   "&profile_delete"]
    ],
 ["VLINE", "vl1"],

["HBOX", "hbplat", ["hsplat", "lplat", "platform"]],
  ["HSPACE", "hsplat"],

["HBOX", "hb0", ["installation_path", "installation_path_show",
        "&installation_path_change"]],

["+LAYOUT", "options_advanced", "vb3"],
["VBOX", "vb3", ["project", "hb0"]],
["+LAYOUT", "project", "hb1"],
["HBOX", "hb1", ["choose_project", "choose_project_combo", "&new_project", "&project_delete"]],


# Installation Page
["+LAYOUT", "page_installation", "vb_pi"],
["VBOX", "vb_pi", ["edit_profile", "settings_advanced", "hl1", "hb4"]],
 ["HLINE", "hl1"],

["+LAYOUT", "edit_profile", "g2"],
["GRID", "g2",
        ["&addedpacks", "&baseveto"],
        ["&pacmanconf", "&repos"]
    ],

["+LAYOUT", "settings_advanced", "vb5"],
["VBOX", "vb5", ["hbi1", "hb5"]],
  ["HBOX", "hbi1", ["mirrorlist", "use_local_mirror"]],
  ["HBOX", "hb5", ["cache", "cache_show", "&cache_change"]],

["+LAYOUT", "mirrorlist", "hb2"],
["HBOX", "hb2", ["&mirrorlist_change"]],

["+LAYOUT", "use_local_mirror", "hb6"],
["HBOX", "hb6", ["l1", "local_mirror", "&local_mirror_change"]],

["HBOX", "hb4", ["hs1", "&install"]],
 ["HSPACE", "hs1"],


# Installation Tweaks Page
["+LAYOUT", "page_tweaks", "vb_pt"],
["VBOX", "vb_pt", ["pacmanops", "vst1", "dlprogress"]],

["+LAYOUT", "pacmanops", "g3"],
  ["GRID", "g3",
        ["&sync", "&update"],
        ["&add", "&remove"]
    ],
  ["VSPACE", "vst1"],


# Larchify Page
["+LAYOUT", "page_larchify", "vb_pl"],
["VBOX", "vb_pl", ["larchify", "vbs1", "hbl2",
        "vbs2", "larchify_advanced", "hbl1"]],
  ["HBOX", "hbl2", ["&locales", "hsl3", "&rcconf"]],
    ["HSPACE", "hsl3"],
  ["VSPACE", "vbs1"],
  ["VSPACE", "vbs2"],

  ["+LAYOUT", "larchify_advanced", "hbl3"],
  ["HBOX", "hbl3", ["vbl1", "hsl2", "vbl2"]],
    ["VBOX", "vbl1", ["&initcpio", "overlay"]],
    ["VBOX", "vbl2", ["ssh", "vsl1", "oldsquash"]],
      ["VSPACE", "vsl1"],
   ["HSPACE", "hsl2"],

["HBOX", "hbl1", ["hsl1", "&build"]],
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
  ["HBOX", "hbm1", ["lm2", "larchpart", "&selectpart", "noformat"]],
  ["HBOX", "hbm5", ["&bootcd", "vlm1", "larchboot"]],
    ["VLINE", "vlm1"],

  ["+LAYOUT", "detection", "vbm3"],
  ["VBOX", "vbm3", ["hbm2a", "hbm2b"]],
    ["HBOX", "hbm2a", ["$device", "$uuid", "$label", "$search"]],
    ["HBOX", "hbm2b", ["lm1", "labelname", "&changelabel"]],


["+LAYOUT", "bootloader", "vbm21"],
["VBOX", "vbm21", ["$grub", "$syslinux", "vsmb1", "hlmb1", "vsmb2", "$none", "lmb1"]],
  ["HLINE", "hlmb1"],
  ["VSPACE", "vsmb1"],
  ["VSPACE", "vsmb2"],

["HBOX", "hbm3", ["&bootlines", "&grubtemplate", "&syslinuxtemplate"]],

["HBOX", "hbm4", ["hsm1", "&make"]],
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

