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
        myform.findChild(pair[0])[pair[1]].connect({message:pair.join("+")},
                                                 signalHandler);
    }
}

// Just to test ...
var bl = [
	["pb_template_browse", "clicked()"],
	["pb_rename_profile", "clicked()"],
	["cb_profile", "currentIndexChanged(QString)"],
	["cb_project", "currentIndexChanged(QString)"],
	["pb_new_project", "clicked()"],
	["pb_install_path_new", "clicked()"]
];
bind(bl);

// Now here's a problem: addItems is not a slot!
var profiles = ["p0", "p1"];
var combobox = myform.findChild("cb_profile");
myform.addItems_cb(combobox, profiles);

var block = 0;
function addItem() {
    block = 1;
    combobox.clear();
    profiles.push("p" + profiles.length);
    myform.addItems_cb(combobox, profiles);
    combobox.setCurrentIndex(-1);
    block = 0;
    combobox.setCurrentIndex(1);
}

myform.findChild("pb_rename_profile")["clicked()"].connect(addItem);
myform.sendLine("Should be connected");
