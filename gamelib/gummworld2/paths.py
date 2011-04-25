#!/usr/bin/env python

# This file is part of Gummworld2.
#
# Gummworld2 is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Gummworld2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with Gummworld2.  If not, see <http://www.gnu.org/licenses/>.


__version__ = '$Id$'
__author__ = 'Gummbum, (c) 2011'


"""paths.py - Path setup for Gummworld2.

!! For game path setup, use the paths.py in the main program directory.

This module sets up the python library path for modules that want to do unit
tests in "if main..." blocks, where gamelib cannot be seen in the current
directory without this special path setup.

Typical usage:
    if __name__ == '__main__':
        import paths
    import gamelib
    ... gamelib module stuff ...
    
    if __name__ == '__main__':
        ... module unit test ...
"""


import os
import sys

progname = sys.argv[0]
progdir = os.path.dirname(progname)
sys.path.insert(0, os.path.normpath(os.path.join(progdir,'..')))
sys.path.insert(0, progdir)
