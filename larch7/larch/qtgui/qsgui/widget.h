#ifndef WIDGET_H
#define WIDGET_H

#include <QWidget>
#include <QComboBox>

class MyWidget : public QWidget
{
    Q_OBJECT

public:
    MyWidget(QString uifile, QWidget *parent = 0);

public slots:
    void newLine(QString line);
    void addItems_cb(QComboBox *widget, const QStringList & texts);
    QWidget *loadUiFile(QString filepath);

signals:
    void sendLine(QString line);
};

#endif // WIDGET_H
