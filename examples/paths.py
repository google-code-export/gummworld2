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


__version__ = '0.4'
__vernum__ = (0,4)


"""paths.py - Path setup for Gummworld2.

Import this at the start of your program to augment the python library path.
"""


import os
import sys

progname = sys.argv[0]
progdir = os.path.dirname(progname)
sys.path.append(os.path.join(progdir,'..'))
sys.path.append(os.path.join(progdir,'..','gamelib'))
