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


__doc__ = """
data.py - Data resource loader for Gummworld2.

Module data:
    * data_py is the absolute path for this module file's directory.
    * data_dir is the root data directory.
    * path is a dict containing lookups for subdirectories of each data type.
"""


import os
from os.path import join as join_path


data_py = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.normpath(join_path(data_py, '..', 'data'))
path = dict(
    font  = join_path(data_dir, 'font'),
    image = join_path(data_dir, 'image'),
    map   = join_path(data_dir, 'map'),
    sound = join_path(data_dir, 'sound'),
    text  = join_path(data_dir, 'text'),
)


def filepath(typ, filename):
    '''Return the path to a file in the data directory.
    '''
    return join_path(path[typ], filename)


def load(typ, filename, mode='rb'):
    '''Open a file in the data directory and return its file handle.

    The mode argument is passed as the second argument to open().
    '''
    return open(filepath(typ, filename), mode)


def load_font(filename):
    """Open a font file from the font dir and return its file handle.
    """
    return load('font', filename)


def load_image(filename):
    """Open an image file from the image dir and return its file handle.
    """
    return load('image', filename)


def load_map(filename):
    """Open a map file from the map dir and return its file handle.
    """
    return load('map', filename)


def load_sound(filename):
    """Open a sound file from the sound dir and return its file handle.
    """
    return load('sound', filename)


def load_text(filename):
    """Open a text file from the text dir and return its file handle.
    """
    return load('text', filename, 'r')
