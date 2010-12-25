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


__version__ = '0.2'
__vernum__ = (0,2)


"""state.py - A class for convenient global access to Gummworld2 run-time objects.
"""


class State(object):
    # objects
    screen = None               # gamelib.Screen
    camera = None               # gamelib.Camera
    
    map = None                  # gamelib.Map
    world = None                # gamelib.World
    
    graphics = None             # gamelib.Graphics
    canvas = None               # gamelib.Canvas
    
    clock = None                # gamelib.GameClock
    events = None               # gamelib.GameEvents, gamelib.EditorEvents, or custom
    clock = None                # gamelib.GameClock
    menu = None                 # gamelib.PopupMenu
    
    # game settings
    running = False
    speed = 4
    scale = 1,1
    
    # map editor settings
    show_grid = False
    show_labels = False
    show_hud = False


# You may add to this if you add your own attributes to State.
default_attrs = [
    'screen',
    'camera',
    'map',
    'world',
    'events',
    'menu',
]
states = {}


def save(name, attrs=default_attrs):
    state_dict = {}
    for attr in attrs:
        if hasattr(State, attr):
            state_dict[attr] = getattr(State, attr)
    states[name] = state_dict


def restore(name, attrs=default_attrs):
    for attr in attrs:
        setattr(State, attr, states[name][attr])

save('main')
restore('main')
