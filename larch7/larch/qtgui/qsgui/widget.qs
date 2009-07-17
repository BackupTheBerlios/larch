// Provide a signal handler which emits appropriate text messages
function signalHandler () {
    /* 'this' should be a string representing the particular signal
    * (including the initiating widget).
    * The argument list needs to be converted to a suitable string form */
    if (arguments.length > 0) {
	args = ":" + arguments[0];
	for (var i = 1; i<arguments.length; i++) {
	    args += "," + arguments[i];
	}
    }
    else args = "";
    if (block != 0) args += "!BLOCK";
    myform.sendLine(this.message + args);
}

function bind(pairs) {
    for (var i = 0; i<pairs.length; i++) {
        var pair = pairs[i];
        var sh = signalHandler;
        var m = pair[2];
        // I could use an alternative, internal, signal handler if the
        // message starts with '+', this is the function which is the
        // next argument
        if ( pair[2][0] == "+" ) {
            sh = pair[3];
            m = m.slice(1);
        }
        myform.findChild(pair[0])[pair[1]].connect({message:m}, sh);
    }
}

// Just to test ...
//***********************************************
// until I install the translation stuff ...
function qsTr(text) { return text; }

var dialog_entry = myform.loadUiFile("dialog_entry.ui");

function getLine(m, e, l, d) {
    if ( !l ) l = qsTr("New value:");
    if ( !d ) l = qsTr("Please enter a new value");
    dialog_entry.findChild("label_description").setText(d);
    dialog_entry.findChild("label").setText(l);
    le = dialog_entry.findChild("lineEdit");
    if ( e ) le.setText(e); else le.clear();
    le.setFocus();
    var args = "!Rejected";
    var r = undefined;
    if ( dialog_entry.exec() ) {
        r = le.text.replace(/\s*/g, "");
        args = ":" + r;
    }
    myform.sendLine(m + args);
    return r;
}

function profile_rename() {
    v = profile_rename.value;
    getLine("-profile_rename#" + v, v,
            qsTr("New name:"), qsTr("Rename the current profile"));
}

// this needs to be a directory browser, possibly validating on the
// existence of an addedpacks file within the selected directory
var profile_new = profile_rename;

function project_new() {
    v = project_new.value;
    item = getLine("-project_new#" + v, v,
            qsTr("Name:"), qsTr("Create a new larch project"));

    // But I may prefer to add items from the main code ...
    if ( item ) pj_addItem(item);
}

// could present the current path as starting text? or rather empty?
var install_path_new = profile_rename;

// messages starting with '+' can be handled within the gui
var bl = [
        ["pb_template_browse", "clicked()", "+1", profile_new],
        ["pb_rename_profile", "clicked()", "+2", profile_rename],
        ["cb_profile", "currentIndexChanged(QString)", "-profile_switch"],
        ["cb_project", "currentIndexChanged(QString)", "-project_switch"],
        ["pb_new_project", "clicked()", "+3", project_new],
        ["pb_install_path_new", "clicked()", "+4", install_path_new]
];
bind(bl);
myform.findChild("cb_profile")["currentIndexChanged(QString)"].connect(
        function (v) { profile_rename.value = v; });
myform.findChild("cb_project")["currentIndexChanged(QString)"].connect(
        function (v) { project_new.value = v; });

var block = 0;
// Now here's a problem: addItems is not a slot!
var profiles = ["p0", "p1"];
var combobox = myform.findChild("cb_profile");
myform.addItems_cb(combobox, profiles);

var projects = ["l1"];
var pj_combobox = myform.findChild("cb_project");
myform.addItems_cb(pj_combobox, projects);
function pj_addItem(item) {
    block = 1;
    pj_combobox.clear();
    projects.push(item);
    myform.addItems_cb(pj_combobox, projects);
    pj_combobox.setCurrentIndex(-1);
    block = 0;
    pj_combobox.setCurrentIndex(1);
}

myform.sendLine("Should be connected");
