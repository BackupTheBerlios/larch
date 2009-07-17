#include "widget.h"
#include <QtUiTools>
#include <QVBoxLayout>

MyWidget::MyWidget(QString uifile, QWidget *parent)
    : QWidget(parent)
{
    QWidget *myWidget = loadUiFile(uifile);
    QVBoxLayout *layout = new QVBoxLayout;
    layout->addWidget(myWidget);
    setLayout(layout);
}

QWidget *MyWidget::loadUiFile(QString filepath)
{
    QUiLoader loader;
    QFile file(filepath);
    if (!file.open(QFile::ReadOnly))
        // handle error
        return 0;
    QWidget *formWidget = loader.load(&file, this);
    file.close();
    return formWidget;
}

void MyWidget::newLine(QString line)
{
    emit sendLine("^+^" + line);
}

void MyWidget::addItems_cb(QComboBox * widget, const QStringList & texts)
{
    widget->addItems(texts);
}
