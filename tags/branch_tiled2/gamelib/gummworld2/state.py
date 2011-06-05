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


__doc__ = """state.py - A class for convenient global access to Gummworld2
run-time objects.

The State class has class variables to hold the core library objects. It also
has save() and restore() static methods to manage context switching.

Programmers may place ad hoc attributes in this class, and leverage the save()
and restore() methods for their own use.
"""


## The default attributes that are saved and restored.
_default_attrs = [
    'world',
    'world_type',
    'map',
    'camera',
]

## The default attributes that are saved and restored when the name argument is
## 'init'.
_init_attrs = [
    'screen', 'world', 'world_type',
    'camera', 'map',
    'clock', 'menu',
    'running', 'speed', 'dt',
    'show_grid', 'show_labels', 'show_hud',
]

# The states dict stores lists of saved objects, keyed by a name. Any valid dict
# key can be used. The contents of this may be changed and read manually or with
# the State.save() and State.restore() static methods.
states = {}


class State(object):
    """state.State
    
    The State class stores runtime objects and settings for easy global access.
    It is not intended to be instantiated.
    
    Descriptions of class attributes:
        name: The name of the current state context. This can be any immutable
            value. Initial value is 'init', and the state is saved so that State
            can be reset via State.restore('init').
        screen: A screen.Screen object, which is a wrapper for the top level
            pygame surface.
        world: A model.World* object used to store game model entities.
        world_type: One of engine.NO_WORLD, engine.SIMPLE_WORLD,
            engine.QUADTREE_WORLD, or engine.PYMUNK_WORLD if State was
            initialized via the Engine class. Else it is None.
        camera: A camera.Camera object.
        map: A map.Map object.
    
    Class variable State.default_attrs holds the list of attributes that are
    saved and restored by default when the static methods State.save() and
    State.restore() are called. Modify default_attrs as desired.

    """
    
    name = 'init'               # name of initial saved state
    
    ## core objects
    
    screen = None               # screen.Screen
    world = None                # model.World
    world_type = None           # engine.*_WORLD
    
    camera = None               # camera.Camera
    camera_target = None        # camera.Camera.target
    map = None                  # map.Map
    
    clock = None                # gameclock.GameClock
    menu = None                 # popup_menu.PopupMenu
    
    ## game settings
    
    speed = 4                   # an arbitrary speed constant
    
    ## map editor settings
    
    show_grid = False
    show_labels = False
    show_hud = False
    
    ## static save/restore methods
    
    # These are initialized to sane values for the bare library. You may modify
    # these for your own purposes.
    default_attrs = _default_attrs
    init_attrs = _init_attrs
    
    @staticmethod
    def save(name, attrs=_default_attrs):
        """state.save() - save a state context by name
        
        The attrs argument is a sequence of strings naming the State attributes
        to save. If attrs is not specified then State.default_attrs is used.
        """
        state_dict = {}
        for attr in attrs:
            if hasattr(State, attr):
                state_dict[attr] = getattr(State, attr)
        states[name] = state_dict

    @staticmethod
    def restore(name, attrs=_default_attrs):
        """state.restore() - restore a state context by name
        
        State.name is set to the value of the name argument.
        
        The attrs argument is a sequence of strings naming the State attributes
        to restore. If attrs is not specified then State.default_attrs is used.
        
        If an object that is being restored has state_restored() method it will
        be called. The method is intended to sync the object with other parts of
        the game that may have updated while it was swapped out.
        """
        if name == 'init' and attrs is _default_attrs:
            attrs = _init_attrs
#        for attr in attrs:
#            setattr(State, attr, states[name][attr])
#        for attr in attrs:
#            obj = getattr(State, attr)
#            if hasattr(obj, 'state_restored'):
#                obj.state_restored()
        for attr in attrs:
            prev = getattr(State, attr)
            rest = states[name][attr]
            setattr(State, attr, rest)
            if hasattr(rest, 'state_restored'):
                rest.state_restored(prev)
        State.name = name


State.save('init', _init_attrs)
