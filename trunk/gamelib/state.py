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


__doc__ = """state.py - A class for convenient global access to Gummworld2 run-time objects.
"""


# You may add to default_attrs if you add your own attributes to State and want
# them saved and restored by default via the static methods.
default_attrs = [
    'camera',
    'world',
    'map',
]

# The states dict stores lists of saved objects, keyed by a name. Any valid dict
# key can be used. The contents of this may be changed and read manually or with
# the State.save() and State.restore() static methods.
states = {}


class State(object):
    
    name = 'init'               # name of initial saved state
    
    # objects
    screen = None               # gamelib.view.Screen
    world = None                # gamelib.model.World
    
    camera = None               # gamelib.Camera
    map = None                  # gamelib.Map
    
    graphics = None             # gamelib.Graphics
    
    clock = None                # gamelib.GameClock
    menu = None                 # gamelib.PopupMenu
    
    # game settings
    running = False             # Engine.run() terminator
    speed = 4                   # an arbitrary speed constant
    dt = 0                      # milliseconds elapsed in previous game tick
    
    # map editor settings
    show_grid = False
    show_labels = False
    show_hud = False
    
    @staticmethod
    def save(name, attrs=default_attrs):
        """save a state by name
        
        The attrs argument is a sequence of strings naming the State attributes
        to save. If attrs is not specified then state.default_attrs is used.
        """
        state_dict = {}
        for attr in attrs:
            if hasattr(State, attr):
                state_dict[attr] = getattr(State, attr)
        states[name] = state_dict

    @staticmethod
    def restore(name, attrs=default_attrs):
        """restore a state context by name
        
        State.name is set to the value of the name argument.
        
        The attrs argument is a sequence of strings naming the State attributes
        to restore. If attrs is not specified then state.default_attrs is used.
        
        If an object that is being restored has state_restored() method it will
        be called. The method is intended to sync the object with other parts of
        the game that may have updated while it was swapped out.
        """
        for attr in attrs:
            setattr(State, attr, states[name][attr])
        for attr in attrs:
            obj = getattr(State, attr)
            if hasattr(obj, 'state_restored'):
                obj.state_restored()
        State.name = name


State.save(State.name)
