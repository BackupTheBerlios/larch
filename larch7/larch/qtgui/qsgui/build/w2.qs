// Provide a signal handler which emits appropriate text messages
function signalHandler () {
    /* 'this' should be a string representing the particular signal
    * (including the initiating widget).
    * The argument list needs to be converted to a suitable string form */
    line = ":args";
    myform.sendLine(this.message + line);
}

print("Hello");

function bind(pairs) {
    print("pairs:"+pairs);
    for (pair in pairs) {
        var widget = pair[0];
        var signal = pair[1];
	print("widget:"+widget);
	print("signal:"+signal);
        //myform.findChild(widget)[signal].connect({message:"mymessage"},
                                                  //widget+"_"+signal},
        //                                         signalHandler);
    }
}

// Just to test ...
bind([["pb_template_browse", "clicked()"]]);

