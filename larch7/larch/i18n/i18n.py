#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# i18n.py

#2009-06-07
# Copyright 2009 Michael Towers

# This file is part of the larch project.
#
#    larch is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    larch is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with larch; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#----------------------------------------------------------------------------

"""
A script, together with i18n2.py, to ease the use of the gettext translation
system with larch. Just run it with the (short) name of your language,
e.g. "fr", as argument.
The steps it performs are roughly given below. If you prefer a gui have a
look at poedit (uses wxwidgets).

1) Generally something like: pygettext.py -p i18n -o larch.pot0 *.py

1a) Create the files for the glade texts, and merge them in. This requires
the gettext tools for 'C':
intltool-extract -l --type=gettext/glade path/to/larch.glade
xgettext -k_ -kN_ -o glade.po tmp/larch.glade.h
# Remove the header:
sed '1,/^$/ d' -i glade.po
cat larch.pot0 glade.po >larch.pot

2) cd i18n ; msginit -i larchin.pot -l de

OR:
2a) to update a po file:

cd i18n ; msgmerge -U larchin.po larchin.pot

3) edit po file

4) generate binary file:
cd i18n ; msgfmt -c -v -o larchin.mo larchin.po

5) move the .mo file to i18n/de/LC_MESSAGES

6) Add to the main program file:

import gettext
gettext.install('larch', 'i18n', unicode=1)

5) Run, e.g.:
LANG=de_DE larchin.py
"""

import sys, os, shutil
from subprocess import call

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
os.chdir(basedir)

if (len(sys.argv) < 2):
    lang = "de"
else:
    lang = sys.argv[1]
print "Generating internationalization for language '%s'\n" % lang
print "    If you wanted a different language run 'i18n.py <language>'"
print "    For example 'i18n.py fr'\n"

dirs = ["run", "modules", "modules/gtk"]
allpy = [os.path.join(d, "*.py") for d in dirs]
call(["mkdir", "-p", "tmp"])
call(["pygettext.py", "-p", "tmp", "-o", "larch.pot0"] + allpy)

# Now add the glade file
gladefile="modules/gtk/larch.glade"
call(["intltool-extract", "-l", "--type=gettext/glade", gladefile])
call(["xgettext", "-k_", "-kN_", "-o", "tmp/glade.po", "tmp/larch.glade.h"])
call(["sed", "1,/^$/ d", "-i", "tmp/glade.po"])
fh = open("i18n/larch.pot", "w")
call(["cat", "tmp/larch.pot0", "tmp/glade.po"], stdout=fh)
fh.close()
call(["rm", "-rf", "tmp"])

os.chdir(thisdir)
langfile = lang + ".po"
pofile = os.path.join(lang, "LC_MESSAGES", langfile)
if os.path.isfile(pofile):
    shutil.copy(pofile, ".")
    call(["msgmerge", "-U", langfile, "larch.pot"])
else:
    call(["sed", "-i", "s|CHARSET|utf-8|", "larch.pot"])
    call(["msginit", "--no-translator", "-i", "larch.pot", "-l", lang])

lf = open("lang", "w")
lf.write(lang)
lf.close()

print "Now edit '%s' and then run 'i18n2.py'" % langfile
