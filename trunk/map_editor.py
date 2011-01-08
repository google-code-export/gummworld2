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


"""map_editor.py - A map editor for Gummworld2.
"""


import pygame
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT
import pymunk

import paths
from gamelib import *


menu_data = (
    'Main',
    'Grid',
    'Labels',
    'HUD',
    (
        'Geometry',
        'Line',
        'Triangle',
        'Quad',
        'Poly',
        'Select Region',
        'Resize',
        'Delete',
    ),
    (
        'Tiling',
        'Load Tileset',
        'Pick from Palette',
        'Pick from Screen',
        'Paint',
        'Erase',
        'Select Region',
        'Fill',
    ),
    (
        'Map',
        'New',
        'Load',
        'Save',
    ),
    'Quit',
)


class MapEditor(Engine):
    
    def __init__(self, screen_size):
        super(MapEditor, self).__init__(resolution=screen_size, frame_speed=0)
        
        # dict to look up movement keys and their corresponding direction on the
        # axis.
        self._Y_KEYS = {K_UP:-1,K_DOWN:1}
        self._X_KEYS = {K_LEFT:-1,K_RIGHT:1}
        
        # These dicts allow robust accumulation of key-presses, and remember the
        # direction*speed. The original step size is preserved so that a KEYUP
        # event removes the right value, even if speed is changed while a key is
        # depressed.
        self.move_y = {}
        self.move_x = {}
        
        # Make some default content and HUD.
        toolkit.make_tiles()
        toolkit.make_hud()
        
    def update(self):
        """Overrides Engine.update."""
        self.update_avatar_position()
        if State.show_hud:
            State.hud.update()
        
    def draw(self):
        """Overrides Engine.draw."""
        # Draw stuff.
        State.camera.interpolate()
        State.screen.clear()
        toolkit.draw_tiles()
        toolkit.draw_labels()
        toolkit.draw_grid()
        if State.show_hud:
            State.hud.draw()
        State.screen.flip()
        
    def update_avatar_position(self):
        # This method updates the avatar's position if any movement keys are
        # currently held down.
        if self.move_y or self.move_x:
            avatar = State.world.avatar
            wx,wy = avatar.position
            wx = reduce(float.__add__, self.move_x.values(), wx)
            wy = reduce(float.__add__, self.move_y.values(), wy)
            # Keep avatar inside world bounds. Note: pymunk.BB.clamp_vect
            # doesn't work because top is less than bottom.
            #avatar.position = State.world.bounding_box.clamp_vect((wx,wy))
            # Instead we'll do this...
            rect = State.world.rect
            wx = max(min(wx,rect.right), rect.left)
            wy = max(min(wy,rect.bottom), rect.top)
            avatar.position = wx,wy
        
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        if key in self._Y_KEYS:
            self.move_y[key] = self._Y_KEYS[key] * State.speed
        elif key in self._X_KEYS:
            self.move_x[key] = self._X_KEYS[key] * State.speed
        
    def on_key_up(self, key, mod):
        # Turn off key-presses.
        if key in self._Y_KEYS:
            del self.move_y[key]
        elif key in self._X_KEYS:
            del self.move_x[key]
        
    def on_mouse_button_up(self, pos, button):
        PopupMenu(menu_data)
        
    def on_user_event(self, e):
        if e.name == 'Main':
            if e.text == 'HUD':
                State.show_hud = not State.show_hud
            elif e.text == 'Grid':
                State.show_grid = not State.show_grid
            elif e.text == 'Labels':
                State.show_labels = not State.show_labels
            elif e.text == 'Quit':
                quit()


if __name__ == '__main__':
    map_editor = MapEditor((600,600))
    map_editor.run()
