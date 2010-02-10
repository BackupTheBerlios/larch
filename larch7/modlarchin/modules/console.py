# console.py - I/O handling for stdio
#
# (c) Copyright 2010 Michael Towers (larch42 at googlemail dot com)
#
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
# 2010.02.09

import sys

class Console:
    def __init__(self, quiet):
        self.quiet = quiet

    def out(self, line, force=False):
        """Output a line - which should not be newline-terminated - of text.
        The output can be adapted to the required format by changing this
        method.
        """
        # This just adds a newline and sends to standard output.
        if force or not self.quiet:
            sys.stdout.write(line + '\n')
            sys.stdout.flush()

    def query_yn(self, message, default=False):
        if self.quiet:
            return default
        for line in message.split('$'):
            out('#? ' + line)
            prompt = _("y(es)|n(o)").split('|')
            if default:
                py = prompt[0].upper()
                pn = prompt[1]
            else:
                py = prompt[0]
                pn = prompt[1].upper()
        resp = raw_input("   [ %s / %s ]: " % prompt).strip()
        if resp:
            i = (prompt[1] if default else prompt[0])[0]
            if i == resp[0].lower():
                return not default
        return default


