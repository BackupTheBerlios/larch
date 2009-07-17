#ifndef IOTHREAD_H
#define IOTHREAD_H

#include <QThread>
#include <QTextStream>

class IOThread : public QThread
{
    Q_OBJECT

public:
    IOThread();
    void run();

private:
    QTextStream *output;

public slots:
    void send(QString line);

signals:
    void inputLineReady(QString line);
};

#endif // IOTHREAD_H
