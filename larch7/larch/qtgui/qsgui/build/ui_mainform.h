/********************************************************************************
** Form generated from reading ui file 'mainform.ui'
**
** Created: Mon Jun 15 06:47:11 2009
**      by: Qt User Interface Compiler version 4.5.1
**
** WARNING! All changes made in this file will be lost when recompiling ui file!
********************************************************************************/

#ifndef UI_MAINFORM_H
#define UI_MAINFORM_H

#include <QtCore/QVariant>
#include <QtGui/QAction>
#include <QtGui/QApplication>
#include <QtGui/QButtonGroup>
#include <QtGui/QComboBox>
#include <QtGui/QFrame>
#include <QtGui/QGridLayout>
#include <QtGui/QGroupBox>
#include <QtGui/QHBoxLayout>
#include <QtGui/QHeaderView>
#include <QtGui/QLabel>
#include <QtGui/QLineEdit>
#include <QtGui/QListWidget>
#include <QtGui/QPushButton>
#include <QtGui/QSpacerItem>
#include <QtGui/QTabWidget>
#include <QtGui/QVBoxLayout>
#include <QtGui/QWidget>

QT_BEGIN_NAMESPACE

class Ui_MainForm
{
public:
    QVBoxLayout *verticalLayout_6;
    QLabel *label;
    QTabWidget *tabWidget;
    QWidget *tab;
    QGridLayout *gridLayout_5;
    QGroupBox *groupBox_2;
    QVBoxLayout *verticalLayout_3;
    QGridLayout *gridLayout;
    QLabel *label_2;
    QComboBox *cb_profile;
    QFrame *line;
    QPushButton *pb_rename_profile;
    QLabel *label_3;
    QPushButton *pb_template_browse;
    QGroupBox *groupBox;
    QVBoxLayout *verticalLayout_2;
    QGroupBox *groupBox_3;
    QVBoxLayout *verticalLayout;
    QHBoxLayout *horizontalLayout;
    QLabel *label_4;
    QComboBox *cb_project;
    QPushButton *pb_new_project;
    QHBoxLayout *horizontalLayout_2;
    QLabel *label_5;
    QLineEdit *entry_installpath;
    QPushButton *pb_install_path_new;
    QSpacerItem *verticalSpacer;
    QWidget *tab_2;
    QVBoxLayout *verticalLayout_4;
    QGroupBox *groupBox_4;
    QHBoxLayout *horizontalLayout_3;
    QPushButton *pushButton_5;
    QPushButton *pushButton_6;
    QPushButton *pushButton_7;
    QGroupBox *groupBox_5;
    QGridLayout *gridLayout_2;
    QLabel *label_6;
    QLineEdit *lineEdit_2;
    QPushButton *pushButton_8;
    QLabel *label_7;
    QLineEdit *lineEdit_3;
    QPushButton *pushButton_9;
    QGroupBox *groupBox_6;
    QHBoxLayout *horizontalLayout_6;
    QVBoxLayout *verticalLayout_7;
    QLabel *label_10;
    QListWidget *listWidget;
    QFrame *line_4;
    QVBoxLayout *verticalLayout_5;
    QGridLayout *gridLayout_3;
    QLabel *label_8;
    QLineEdit *lineEdit_4;
    QPushButton *pushButton_11;
    QLabel *label_9;
    QLineEdit *lineEdit_5;
    QPushButton *pushButton_12;
    QFrame *line_3;
    QGridLayout *gridLayout_4;
    QPushButton *pushButton_13;
    QPushButton *pushButton_14;
    QPushButton *pushButton_15;
    QPushButton *pushButton_16;
    QFrame *line_2;
    QHBoxLayout *horizontalLayout_5;
    QSpacerItem *horizontalSpacer;
    QPushButton *pushButton_10;
    QWidget *tab_3;
    QWidget *tab_4;
    QHBoxLayout *horizontalLayout_4;

    void setupUi(QWidget *MainForm)
    {
        if (MainForm->objectName().isEmpty())
            MainForm->setObjectName(QString::fromUtf8("MainForm"));
        MainForm->resize(560, 557);
        QSizePolicy sizePolicy(QSizePolicy::MinimumExpanding, QSizePolicy::MinimumExpanding);
        sizePolicy.setHorizontalStretch(0);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(MainForm->sizePolicy().hasHeightForWidth());
        MainForm->setSizePolicy(sizePolicy);
        MainForm->setMinimumSize(QSize(100, 0));
        QFont font;
        font.setPointSize(10);
        MainForm->setFont(font);
        MainForm->setWindowTitle(QString::fromUtf8("larch"));
        verticalLayout_6 = new QVBoxLayout(MainForm);
        verticalLayout_6->setObjectName(QString::fromUtf8("verticalLayout_6"));
        label = new QLabel(MainForm);
        label->setObjectName(QString::fromUtf8("label"));
        label->setTextFormat(Qt::RichText);

        verticalLayout_6->addWidget(label);

        tabWidget = new QTabWidget(MainForm);
        tabWidget->setObjectName(QString::fromUtf8("tabWidget"));
        tab = new QWidget();
        tab->setObjectName(QString::fromUtf8("tab"));
        gridLayout_5 = new QGridLayout(tab);
        gridLayout_5->setObjectName(QString::fromUtf8("gridLayout_5"));
        groupBox_2 = new QGroupBox(tab);
        groupBox_2->setObjectName(QString::fromUtf8("groupBox_2"));
        verticalLayout_3 = new QVBoxLayout(groupBox_2);
        verticalLayout_3->setObjectName(QString::fromUtf8("verticalLayout_3"));
        gridLayout = new QGridLayout();
        gridLayout->setObjectName(QString::fromUtf8("gridLayout"));
        label_2 = new QLabel(groupBox_2);
        label_2->setObjectName(QString::fromUtf8("label_2"));
        label_2->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        gridLayout->addWidget(label_2, 0, 0, 1, 1);

        cb_profile = new QComboBox(groupBox_2);
        cb_profile->setObjectName(QString::fromUtf8("cb_profile"));

        gridLayout->addWidget(cb_profile, 0, 1, 1, 1);

        line = new QFrame(groupBox_2);
        line->setObjectName(QString::fromUtf8("line"));
        line->setFrameShape(QFrame::VLine);
        line->setFrameShadow(QFrame::Sunken);

        gridLayout->addWidget(line, 0, 2, 2, 1);

        pb_rename_profile = new QPushButton(groupBox_2);
        pb_rename_profile->setObjectName(QString::fromUtf8("pb_rename_profile"));

        gridLayout->addWidget(pb_rename_profile, 0, 3, 1, 1);

        label_3 = new QLabel(groupBox_2);
        label_3->setObjectName(QString::fromUtf8("label_3"));
        label_3->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        gridLayout->addWidget(label_3, 1, 0, 1, 1);

        pb_template_browse = new QPushButton(groupBox_2);
        pb_template_browse->setObjectName(QString::fromUtf8("pb_template_browse"));

        gridLayout->addWidget(pb_template_browse, 1, 1, 1, 1);


        verticalLayout_3->addLayout(gridLayout);


        gridLayout_5->addWidget(groupBox_2, 0, 0, 1, 1);

        groupBox = new QGroupBox(tab);
        groupBox->setObjectName(QString::fromUtf8("groupBox"));
        groupBox->setFlat(false);
        groupBox->setCheckable(true);
        groupBox->setChecked(false);
        verticalLayout_2 = new QVBoxLayout(groupBox);
        verticalLayout_2->setObjectName(QString::fromUtf8("verticalLayout_2"));
        groupBox_3 = new QGroupBox(groupBox);
        groupBox_3->setObjectName(QString::fromUtf8("groupBox_3"));
        verticalLayout = new QVBoxLayout(groupBox_3);
        verticalLayout->setObjectName(QString::fromUtf8("verticalLayout"));
        horizontalLayout = new QHBoxLayout();
        horizontalLayout->setObjectName(QString::fromUtf8("horizontalLayout"));
        label_4 = new QLabel(groupBox_3);
        label_4->setObjectName(QString::fromUtf8("label_4"));
        label_4->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        horizontalLayout->addWidget(label_4);

        cb_project = new QComboBox(groupBox_3);
        cb_project->setObjectName(QString::fromUtf8("cb_project"));

        horizontalLayout->addWidget(cb_project);

        pb_new_project = new QPushButton(groupBox_3);
        pb_new_project->setObjectName(QString::fromUtf8("pb_new_project"));

        horizontalLayout->addWidget(pb_new_project);


        verticalLayout->addLayout(horizontalLayout);


        verticalLayout_2->addWidget(groupBox_3);

        horizontalLayout_2 = new QHBoxLayout();
        horizontalLayout_2->setObjectName(QString::fromUtf8("horizontalLayout_2"));
        label_5 = new QLabel(groupBox);
        label_5->setObjectName(QString::fromUtf8("label_5"));
        label_5->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        horizontalLayout_2->addWidget(label_5);

        entry_installpath = new QLineEdit(groupBox);
        entry_installpath->setObjectName(QString::fromUtf8("entry_installpath"));
        entry_installpath->setReadOnly(true);

        horizontalLayout_2->addWidget(entry_installpath);

        pb_install_path_new = new QPushButton(groupBox);
        pb_install_path_new->setObjectName(QString::fromUtf8("pb_install_path_new"));

        horizontalLayout_2->addWidget(pb_install_path_new);


        verticalLayout_2->addLayout(horizontalLayout_2);


        gridLayout_5->addWidget(groupBox, 3, 0, 1, 1);

        verticalSpacer = new QSpacerItem(20, 148, QSizePolicy::Minimum, QSizePolicy::Expanding);

        gridLayout_5->addItem(verticalSpacer, 2, 0, 1, 1);

        tabWidget->addTab(tab, QString());
        tab_2 = new QWidget();
        tab_2->setObjectName(QString::fromUtf8("tab_2"));
        verticalLayout_4 = new QVBoxLayout(tab_2);
        verticalLayout_4->setObjectName(QString::fromUtf8("verticalLayout_4"));
        groupBox_4 = new QGroupBox(tab_2);
        groupBox_4->setObjectName(QString::fromUtf8("groupBox_4"));
        horizontalLayout_3 = new QHBoxLayout(groupBox_4);
        horizontalLayout_3->setObjectName(QString::fromUtf8("horizontalLayout_3"));
        pushButton_5 = new QPushButton(groupBox_4);
        pushButton_5->setObjectName(QString::fromUtf8("pushButton_5"));

        horizontalLayout_3->addWidget(pushButton_5);

        pushButton_6 = new QPushButton(groupBox_4);
        pushButton_6->setObjectName(QString::fromUtf8("pushButton_6"));

        horizontalLayout_3->addWidget(pushButton_6);

        pushButton_7 = new QPushButton(groupBox_4);
        pushButton_7->setObjectName(QString::fromUtf8("pushButton_7"));

        horizontalLayout_3->addWidget(pushButton_7);


        verticalLayout_4->addWidget(groupBox_4);

        groupBox_5 = new QGroupBox(tab_2);
        groupBox_5->setObjectName(QString::fromUtf8("groupBox_5"));
        gridLayout_2 = new QGridLayout(groupBox_5);
        gridLayout_2->setObjectName(QString::fromUtf8("gridLayout_2"));
        label_6 = new QLabel(groupBox_5);
        label_6->setObjectName(QString::fromUtf8("label_6"));
        label_6->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        gridLayout_2->addWidget(label_6, 0, 0, 1, 1);

        lineEdit_2 = new QLineEdit(groupBox_5);
        lineEdit_2->setObjectName(QString::fromUtf8("lineEdit_2"));

        gridLayout_2->addWidget(lineEdit_2, 0, 1, 1, 1);

        pushButton_8 = new QPushButton(groupBox_5);
        pushButton_8->setObjectName(QString::fromUtf8("pushButton_8"));

        gridLayout_2->addWidget(pushButton_8, 0, 2, 1, 1);

        label_7 = new QLabel(groupBox_5);
        label_7->setObjectName(QString::fromUtf8("label_7"));

        gridLayout_2->addWidget(label_7, 1, 0, 1, 1);

        lineEdit_3 = new QLineEdit(groupBox_5);
        lineEdit_3->setObjectName(QString::fromUtf8("lineEdit_3"));

        gridLayout_2->addWidget(lineEdit_3, 1, 1, 1, 1);

        pushButton_9 = new QPushButton(groupBox_5);
        pushButton_9->setObjectName(QString::fromUtf8("pushButton_9"));

        gridLayout_2->addWidget(pushButton_9, 1, 2, 1, 1);


        verticalLayout_4->addWidget(groupBox_5);

        groupBox_6 = new QGroupBox(tab_2);
        groupBox_6->setObjectName(QString::fromUtf8("groupBox_6"));
        groupBox_6->setFlat(false);
        groupBox_6->setCheckable(true);
        groupBox_6->setChecked(false);
        horizontalLayout_6 = new QHBoxLayout(groupBox_6);
        horizontalLayout_6->setObjectName(QString::fromUtf8("horizontalLayout_6"));
        verticalLayout_7 = new QVBoxLayout();
        verticalLayout_7->setObjectName(QString::fromUtf8("verticalLayout_7"));
        label_10 = new QLabel(groupBox_6);
        label_10->setObjectName(QString::fromUtf8("label_10"));
        label_10->setWordWrap(true);

        verticalLayout_7->addWidget(label_10);

        listWidget = new QListWidget(groupBox_6);
        QListWidgetItem *__qlistwidgetitem = new QListWidgetItem(listWidget);
        __qlistwidgetitem->setText(QString::fromUtf8("core"));
        __qlistwidgetitem->setCheckState(Qt::Unchecked);
        __qlistwidgetitem->setFlags(Qt::ItemIsUserCheckable|Qt::ItemIsEnabled);
        QListWidgetItem *__qlistwidgetitem1 = new QListWidgetItem(listWidget);
        __qlistwidgetitem1->setText(QString::fromUtf8("extra"));
        __qlistwidgetitem1->setCheckState(Qt::Unchecked);
        __qlistwidgetitem1->setFlags(Qt::ItemIsUserCheckable|Qt::ItemIsEnabled);
        QListWidgetItem *__qlistwidgetitem2 = new QListWidgetItem(listWidget);
        __qlistwidgetitem2->setText(QString::fromUtf8("community"));
        __qlistwidgetitem2->setCheckState(Qt::Unchecked);
        __qlistwidgetitem2->setFlags(Qt::ItemIsUserCheckable|Qt::ItemIsEnabled);
        QListWidgetItem *__qlistwidgetitem3 = new QListWidgetItem(listWidget);
        __qlistwidgetitem3->setCheckState(Qt::Unchecked);
        __qlistwidgetitem3->setFlags(Qt::ItemIsUserCheckable|Qt::ItemIsEnabled);
        listWidget->setObjectName(QString::fromUtf8("listWidget"));
        QSizePolicy sizePolicy1(QSizePolicy::Fixed, QSizePolicy::Fixed);
        sizePolicy1.setHorizontalStretch(0);
        sizePolicy1.setVerticalStretch(0);
        sizePolicy1.setHeightForWidth(listWidget->sizePolicy().hasHeightForWidth());
        listWidget->setSizePolicy(sizePolicy1);
        listWidget->setMinimumSize(QSize(100, 100));
        listWidget->setMaximumSize(QSize(150, 150));

        verticalLayout_7->addWidget(listWidget);


        horizontalLayout_6->addLayout(verticalLayout_7);

        line_4 = new QFrame(groupBox_6);
        line_4->setObjectName(QString::fromUtf8("line_4"));
        line_4->setFrameShape(QFrame::VLine);
        line_4->setFrameShadow(QFrame::Sunken);

        horizontalLayout_6->addWidget(line_4);

        verticalLayout_5 = new QVBoxLayout();
        verticalLayout_5->setObjectName(QString::fromUtf8("verticalLayout_5"));
        gridLayout_3 = new QGridLayout();
        gridLayout_3->setObjectName(QString::fromUtf8("gridLayout_3"));
        label_8 = new QLabel(groupBox_6);
        label_8->setObjectName(QString::fromUtf8("label_8"));
        label_8->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        gridLayout_3->addWidget(label_8, 0, 0, 1, 1);

        lineEdit_4 = new QLineEdit(groupBox_6);
        lineEdit_4->setObjectName(QString::fromUtf8("lineEdit_4"));

        gridLayout_3->addWidget(lineEdit_4, 0, 1, 1, 1);

        pushButton_11 = new QPushButton(groupBox_6);
        pushButton_11->setObjectName(QString::fromUtf8("pushButton_11"));

        gridLayout_3->addWidget(pushButton_11, 0, 2, 1, 1);

        label_9 = new QLabel(groupBox_6);
        label_9->setObjectName(QString::fromUtf8("label_9"));
        label_9->setAlignment(Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter);

        gridLayout_3->addWidget(label_9, 1, 0, 1, 1);

        lineEdit_5 = new QLineEdit(groupBox_6);
        lineEdit_5->setObjectName(QString::fromUtf8("lineEdit_5"));

        gridLayout_3->addWidget(lineEdit_5, 1, 1, 1, 1);

        pushButton_12 = new QPushButton(groupBox_6);
        pushButton_12->setObjectName(QString::fromUtf8("pushButton_12"));

        gridLayout_3->addWidget(pushButton_12, 1, 2, 1, 1);


        verticalLayout_5->addLayout(gridLayout_3);

        line_3 = new QFrame(groupBox_6);
        line_3->setObjectName(QString::fromUtf8("line_3"));
        line_3->setFrameShape(QFrame::HLine);
        line_3->setFrameShadow(QFrame::Sunken);

        verticalLayout_5->addWidget(line_3);

        gridLayout_4 = new QGridLayout();
        gridLayout_4->setObjectName(QString::fromUtf8("gridLayout_4"));
        pushButton_13 = new QPushButton(groupBox_6);
        pushButton_13->setObjectName(QString::fromUtf8("pushButton_13"));
        QSizePolicy sizePolicy2(QSizePolicy::Minimum, QSizePolicy::Fixed);
        sizePolicy2.setHorizontalStretch(0);
        sizePolicy2.setVerticalStretch(0);
        sizePolicy2.setHeightForWidth(pushButton_13->sizePolicy().hasHeightForWidth());
        pushButton_13->setSizePolicy(sizePolicy2);

        gridLayout_4->addWidget(pushButton_13, 0, 0, 1, 1);

        pushButton_14 = new QPushButton(groupBox_6);
        pushButton_14->setObjectName(QString::fromUtf8("pushButton_14"));

        gridLayout_4->addWidget(pushButton_14, 0, 1, 1, 1);

        pushButton_15 = new QPushButton(groupBox_6);
        pushButton_15->setObjectName(QString::fromUtf8("pushButton_15"));

        gridLayout_4->addWidget(pushButton_15, 1, 0, 1, 1);

        pushButton_16 = new QPushButton(groupBox_6);
        pushButton_16->setObjectName(QString::fromUtf8("pushButton_16"));

        gridLayout_4->addWidget(pushButton_16, 1, 1, 1, 1);


        verticalLayout_5->addLayout(gridLayout_4);


        horizontalLayout_6->addLayout(verticalLayout_5);


        verticalLayout_4->addWidget(groupBox_6);

        line_2 = new QFrame(tab_2);
        line_2->setObjectName(QString::fromUtf8("line_2"));
        line_2->setFrameShape(QFrame::HLine);
        line_2->setFrameShadow(QFrame::Sunken);

        verticalLayout_4->addWidget(line_2);

        horizontalLayout_5 = new QHBoxLayout();
        horizontalLayout_5->setObjectName(QString::fromUtf8("horizontalLayout_5"));
        horizontalSpacer = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        horizontalLayout_5->addItem(horizontalSpacer);

        pushButton_10 = new QPushButton(tab_2);
        pushButton_10->setObjectName(QString::fromUtf8("pushButton_10"));

        horizontalLayout_5->addWidget(pushButton_10);


        verticalLayout_4->addLayout(horizontalLayout_5);

        tabWidget->addTab(tab_2, QString());
        tab_3 = new QWidget();
        tab_3->setObjectName(QString::fromUtf8("tab_3"));
        tabWidget->addTab(tab_3, QString());
        tab_4 = new QWidget();
        tab_4->setObjectName(QString::fromUtf8("tab_4"));
        tabWidget->addTab(tab_4, QString());

        verticalLayout_6->addWidget(tabWidget);

        horizontalLayout_4 = new QHBoxLayout();
        horizontalLayout_4->setObjectName(QString::fromUtf8("horizontalLayout_4"));

        verticalLayout_6->addLayout(horizontalLayout_4);


        retranslateUi(MainForm);

        tabWidget->setCurrentIndex(0);


        QMetaObject::connectSlotsByName(MainForm);
    } // setupUi

    void retranslateUi(QWidget *MainForm)
    {
        label->setText(QApplication::translate("MainForm", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Sans Serif'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:20pt; font-weight:600; font-style:italic; color:#55aa00;\">larch</span><span style=\" font-size:16pt; color:#55aa00;\"> - Live Arch Linux Construction Kit</span></p></body></html>", 0, QApplication::UnicodeUTF8));
        groupBox_2->setTitle(QApplication::translate("MainForm", "Profile:", 0, QApplication::UnicodeUTF8));
        label_2->setText(QApplication::translate("MainForm", "Choose Existing Profile:", 0, QApplication::UnicodeUTF8));
        pb_rename_profile->setText(QApplication::translate("MainForm", "Rename", 0, QApplication::UnicodeUTF8));
        label_3->setText(QApplication::translate("MainForm", "New Profile:", 0, QApplication::UnicodeUTF8));
        pb_template_browse->setText(QApplication::translate("MainForm", "Browse for Template", 0, QApplication::UnicodeUTF8));
        groupBox->setTitle(QApplication::translate("MainForm", "Advanced Options", 0, QApplication::UnicodeUTF8));
        groupBox_3->setTitle(QApplication::translate("MainForm", "Project:", 0, QApplication::UnicodeUTF8));
        label_4->setText(QApplication::translate("MainForm", "Choose Existing Project:", 0, QApplication::UnicodeUTF8));
        pb_new_project->setText(QApplication::translate("MainForm", "New Project", 0, QApplication::UnicodeUTF8));
        label_5->setText(QApplication::translate("MainForm", "Installation Path:", 0, QApplication::UnicodeUTF8));
        pb_install_path_new->setText(QApplication::translate("MainForm", "Change", 0, QApplication::UnicodeUTF8));
        tabWidget->setTabText(tabWidget->indexOf(tab), QApplication::translate("MainForm", "Project Settings", 0, QApplication::UnicodeUTF8));
        groupBox_4->setTitle(QApplication::translate("MainForm", "Edit Profile", 0, QApplication::UnicodeUTF8));
        pushButton_5->setText(QApplication::translate("MainForm", "Edit 'addedpacks'", 0, QApplication::UnicodeUTF8));
        pushButton_6->setText(QApplication::translate("MainForm", "Edit 'baseveto'", 0, QApplication::UnicodeUTF8));
        pushButton_7->setText(QApplication::translate("MainForm", "Edit pacman.conf template", 0, QApplication::UnicodeUTF8));
        groupBox_5->setTitle(QApplication::translate("MainForm", "Pacman Sources", 0, QApplication::UnicodeUTF8));
        label_6->setText(QApplication::translate("MainForm", "larch Repository:", 0, QApplication::UnicodeUTF8));
        pushButton_8->setText(QApplication::translate("MainForm", "Change", 0, QApplication::UnicodeUTF8));
        label_7->setText(QApplication::translate("MainForm", "Arch Mirror:", 0, QApplication::UnicodeUTF8));
        pushButton_9->setText(QApplication::translate("MainForm", "Change", 0, QApplication::UnicodeUTF8));
        groupBox_6->setTitle(QApplication::translate("MainForm", "Advanced Options", 0, QApplication::UnicodeUTF8));
        label_10->setText(QApplication::translate("MainForm", "Synchronize to host db", 0, QApplication::UnicodeUTF8));

        const bool __sortingEnabled = listWidget->isSortingEnabled();
        listWidget->setSortingEnabled(false);
        QListWidgetItem *___qlistwidgetitem = listWidget->item(3);
        ___qlistwidgetitem->setText(QApplication::translate("MainForm", "larch", 0, QApplication::UnicodeUTF8));
        listWidget->setSortingEnabled(__sortingEnabled);

        label_8->setText(QApplication::translate("MainForm", "Package Cache:", 0, QApplication::UnicodeUTF8));
        pushButton_11->setText(QApplication::translate("MainForm", "Change", 0, QApplication::UnicodeUTF8));
        label_9->setText(QApplication::translate("MainForm", "Package-db Source:", 0, QApplication::UnicodeUTF8));
        pushButton_12->setText(QApplication::translate("MainForm", "Change", 0, QApplication::UnicodeUTF8));
        pushButton_13->setText(QApplication::translate("MainForm", "Synchronize db", 0, QApplication::UnicodeUTF8));
        pushButton_14->setText(QApplication::translate("MainForm", "Update / Add package    [-U]", 0, QApplication::UnicodeUTF8));
        pushButton_15->setText(QApplication::translate("MainForm", "Add package(s)    [-S]", 0, QApplication::UnicodeUTF8));
        pushButton_16->setText(QApplication::translate("MainForm", "Remove package(s)    [-Rs]", 0, QApplication::UnicodeUTF8));
        pushButton_10->setText(QApplication::translate("MainForm", "Install", 0, QApplication::UnicodeUTF8));
        tabWidget->setTabText(tabWidget->indexOf(tab_2), QApplication::translate("MainForm", "Installation", 0, QApplication::UnicodeUTF8));
        tabWidget->setTabText(tabWidget->indexOf(tab_3), QApplication::translate("MainForm", "Larchify", 0, QApplication::UnicodeUTF8));
        tabWidget->setTabText(tabWidget->indexOf(tab_4), QApplication::translate("MainForm", "Prepare Medium", 0, QApplication::UnicodeUTF8));
        Q_UNUSED(MainForm);
    } // retranslateUi

};

namespace Ui {
    class MainForm: public Ui_MainForm {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MAINFORM_H
