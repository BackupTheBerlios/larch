// Provide a signal handler which emits appropriate text messages
function signalHandler () {
    /* 'this' should be a string representing the particular signal
    * (including the initiating widget).
    * The argument list needs to be converted to a suitable string form */
    line = ":args";
    myform.sendLine(this.message + line);
}


function bind(pairs) {
    for (pair in pairs) {
        var widget = pair[0];
        var signal = pair[1];
        myform.findChild(widget)[signal].connect({message:"mymessage"},
                                                  //widget+"_"+signal},
                                                 signalHandler);
    }
}

// Just to test ...
bind([["pb_template_browse", "clicked()"]]);

