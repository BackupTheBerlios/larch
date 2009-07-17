# -------------------------------------------------
# Project created by QtCreator 2009-06-14T22:06:03
# -------------------------------------------------
TRANSLATIONS = qsgui_de.ts
QT += script \
    scripttools
CONFIG += uitools
TARGET = qsgui
TEMPLATE = app
SOURCES += main.cpp \
    widget.cpp \
    iothread.cpp
HEADERS += widget.h \
    iothread.h
FORMS += mainform.ui \
    dialog_entry.ui
OTHER_FILES += widget.qs
