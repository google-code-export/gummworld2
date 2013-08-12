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
__author__ = 'Gummbum, (c) 2011-2013'


__doc__ = """data.py - Data resource loader for Gummworld2.

Module data may be used directly, but use of the module functions is preferred:
    *   data_py is the absolute path for this module file's directory.
    *   data_dir is the root data directory.
    *   subdirs is a dict(name=subdir) for looking up resource sub-directories
        by name. name is simply an abstract type or description.
    *   paths is a "cooked" dict containing lookups for subdirectories of each
        data type.
"""


import os
from os.path import join as join_path


def set_data_dir(base):
    """Set the base data directory for game resources.
    
    base may be a relative or absolute path. It will be converted to an absolute
    path and then normalized.
    
    Calling this function changes the base data directory. The full path to a
    data resource is constructed by joining data_dir and a subdir.
    
    The default data directory is '../../data', relative to the path of this
    module file.
    
    NOTE: Call this early, before attempting to construct any library objects or
    load resources.
    
    Any previously loaded resources are unaffected. However, there may be
    side-effects, for example memory leaks if a user-defined caching mechanism
    uses data paths to fetch resources from cache.
    """
    global data_dir
    data_dir = os.path.abspath(os.path.normpath(base))
    paths.clear()
    for name,value in subdirs.items():
        paths[name] = join_path(data_dir,value)


def set_subdir(name, subdir):
    """Set or add a new sub-directory for game resources.
    
    name is the unique key used to look up the resource location. subdir is the
    path component(s) to append to the data_path base directory.
    
    subdir is assumed to be a relative path and is taken at face value. No
    sanity or access checks are performed.
    """
    subdirs[name] = subdir
    paths[name] = join_path(data_dir,subdir)


def filepath(typ, filename):
    '''Return the path to a file in the data directory.
    '''
    return join_path(paths[typ], filename)


def relpath(filename):
    '''Return the file path relative to data_dir.
    
    For example:
        # data.data_dir is "/games/pong/data"
        filename = "/games/pong/data/image/my.png"
        relname = data.relpath(filename)
        # relname is "image/my.png"
    '''
    return os.path.relpath(filename, data_dir)


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


data_py = os.path.abspath(os.path.dirname(__file__))
##data_dir = os.path.normpath(join_path(data_py, '..', '..', 'data'))
data_dir = None
subdirs = dict(
   font  = 'font',
    image = 'image',
    map   = 'map',
    sound = 'sound',
    text  = 'text',
    theme = 'themes',
)
paths = {}

set_data_dir(join_path(data_py,'..','..','data'))
