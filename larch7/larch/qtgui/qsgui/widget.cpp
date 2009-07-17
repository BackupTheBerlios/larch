#include "widget.h"
#include <QtUiTools>
#include <QVBoxLayout>


// Maybe make MyWidget a subclass of, say, UiWidget, which would
// include the general functionality (everything except 'newLine'),
// so that it can be used in other forms.
// However, it may be that I only need the loadUiFile method, in
// which case I can use the existing instance of MyWidget.

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

void MyWidget::addItems_cb(QComboBox * widget, const QStringList & texts)
{
    widget->addItems(texts);
}

void MyWidget::newLine(QString line)
{
    emit sendLine("^+^" + line);
}


// This is still under consideration ...
// I might consider using a QTabBar with directory list (a bit like the gtk
// widget), rather than the tree, which looks a bit lacking in documentation!
// The QTabBar is, however, not available in Designer.
FSBrowser::FSBrowser(const QStringList & nameFilters, QDir::Filters filters, QDir::SortFlags sort,QWidget *parent)
    : QTreeView(parent)
{
    QDirModel *model = new QDirModel(this);
    setModel(model);
}

FSBrowser::setMode(QString mode)
{
    QDir::Filters f = QDir::AllDirs | QDir::NoDotAndDotDot;
    if ( ! mode.contains('d') ) f |= QDir::Files;
    if ( showHidden ) f |= QDir::Hidden;
    model->setFilter(f);
    // Do I need to refresh something?
}

/*
QItemSelectionModel * selmodel = selectionModel();

QString QDirModel::filePath ( const QModelIndex & index ) const
QFileSystemModel might be better than QDirModel?
*/
