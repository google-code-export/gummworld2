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


__version__ = '0.1'
__vernum__ = (0,1)


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
    speed = 2
    
    # map editor settings
    show_grid = False
    show_labels = False
    show_hud = False
