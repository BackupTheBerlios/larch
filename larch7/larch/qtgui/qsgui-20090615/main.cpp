#include <QtGui/QApplication>
#include <QtScript>
#include <QtScriptTools>
#include "iothread.h"
#include "widget.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    MyWidget w("mainform.ui");

    IOThread io;
    QObject::connect(&io, SIGNAL(inputLineReady(QString)),
                      &w, SLOT(newLine(QString)));
    QObject::connect(&w, SIGNAL(sendLine(QString)),
                      &io, SLOT(send(QString)));
    io.start();

    QScriptEngine engine;

    QScriptEngineDebugger debugger;
    debugger.attachTo(&engine);

    QScriptValue mainformValue = engine.newQObject(&w);
    engine.globalObject().setProperty("myform", mainformValue);

    QString fileName = "widget.qs";
    QFile scriptFile(fileName);
    if (!scriptFile.open(QIODevice::ReadOnly))
        // handle error
        return 1;
    QTextStream stream(&scriptFile);
    QString contents = stream.readAll();
    scriptFile.close();
    engine.evaluate(contents, fileName);

    // A start signal
    io.send("^*^");

    w.show();
    int result = a.exec();
    // A finishing signal
    io.send("^_^");
    // Ideally I would inject a terminating string into the input
    // buffer, so that the input thread would not be abruptly terminated.
    // And then
    io.wait(500);
    return result;
}
