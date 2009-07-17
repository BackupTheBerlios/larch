#include "iothread.h"
// Something like this is needed - in its own thread - to read from stdin.
// This allows the main event loop to run unblocked. The signal-slot mechanism
// handles the coupling of the threads.

IOThread::IOThread()
{
    output = new QTextStream(stdout);
}

void IOThread::run()
{
    QTextStream stream(stdin);
    QString line;
    do {
        line = stream.readLine();
        emit inputLineReady(line);
    } while (line != "^_^");
}

void IOThread::send(QString line)
{
    *output << line << endl;
}
