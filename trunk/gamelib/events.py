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


"""events.py - Event handlers for Gummworld2.
"""


import pygame
from pygame.locals import *

from state import State
from popup_menu import PopupMenu
from pygame_utils import circumference_point


class PlayerEvents(object):
    
    def __init__(self):
        # Movement keys and their corresponding direction on the axis
        self._Y_KEYS = {K_UP:-1,K_DOWN:1}
        self._X_KEYS = {K_LEFT:-1,K_RIGHT:1}
        # dicts allow robust accumulation of key-presses, and remember the
        # direction*speed. The original step size is preserved so that a
        # KEYUP event removes the right value, even if State.speed is changed
        # while a key is depressed.
        self.move_y = {}
        self.move_x = {}
    
    def get(self):
        # Interpret each event.
        for e in pygame.event.get():
            self.interpret(e)
        # If the dicts have key-presses, adjust the camera position by them.
        if self.move_y:
            ## Step the avatar in the direction of avatar.rotation.
            sumy = 0.0
            for y in self.move_y.values():
                sumy += y
            avatar = State.world.avatar
            avatar.position = circumference_point(
                avatar.position, avatar.speed*sumy, avatar.rotation)
        if self.move_x:
            ## Turn the avatar.
            for x in self.move_x.values():
                State.world.avatar.rotation += x
            State.world.avatar.rotation %= 360.0

    def interpret(self, e):
        if e.type == KEYDOWN:
            # Turn on key-presses.
            if e.key in self._Y_KEYS:
                self.move_y[e.key] = self._Y_KEYS[e.key] * State.speed
            elif e.key in self._X_KEYS:
                self.move_x[e.key] = self._X_KEYS[e.key] * State.speed
            elif e.key == K_EQUALS:
                State.world.avatar.rotation = 0.0
        elif e.type == KEYUP:
            # Turn off key-presses.
            if e.key in self._Y_KEYS:
                del self.move_y[e.key]
            elif e.key in self._X_KEYS:
                del self.move_x[e.key]


class EditorEvents(object):
    
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
    
    def __init__(self):
        # Movement keys and their corresponding direction on the axis
        self._Y_KEYS = {K_UP:-1,K_DOWN:1}
        self._X_KEYS = {K_LEFT:-1,K_RIGHT:1}
        # dicts allow robust accumulation of key-presses, and remember the
        # direction*speed. The original step size is preserved so that a
        # KEYUP event removes the right value, even if State.speed is changed
        # while a key is depressed.
        self.move_y = {}
        self.move_x = {}
    
    def get(self):
        # Interpret each event.
        for e in pygame.event.get():
            self.interpret(e)
        # If the dicts have key-presses, adjust the camera position by them.
        if self.move_y or self.move_x:
            avatar = State.world.avatar
            wx,wy = avatar.position
            for y in self.move_y.values():
                wy += y
            for x in self.move_x.values():
                wx += x
            ## Keep avatar inside world bounds.
# This doesn't work anymore because top is less than bottom.
#            avatar.position = State.world.bounding_box.clamp_vect((wx,wy))
            rect = State.world.rect
            avatar.position.x = max(min(wx,rect.right),rect.left)
            avatar.position.y = max(min(wy,rect.bottom),rect.top)

    def interpret(self, e):
        if e.type == KEYDOWN:
            # Turn on key-presses.
            if e.key in self._Y_KEYS:
                self.move_y[e.key] = self._Y_KEYS[e.key] * State.speed
            elif e.key in self._X_KEYS:
                self.move_x[e.key] = self._X_KEYS[e.key] * State.speed
        elif e.type == KEYUP:
            # Turn off key-presses.
            if e.key in self._Y_KEYS:
                del self.move_y[e.key]
            elif e.key in self._X_KEYS:
                del self.move_x[e.key]
        elif e.type == MOUSEBUTTONUP:
            PopupMenu(self.menu_data)
        elif e.type == USEREVENT and e.code == 'MENU':
            self.interpret_menu(e)
    
    def interpret_menu(self, e):
#        print 'menu event: %s.%d: %s' % (e.name,e.item_id,e.text)
        if e.name == 'Main':
            if e.text == 'HUD':
                State.show_hud = not State.show_hud
            elif e.text == 'Grid':
                State.show_grid = not State.show_grid
            elif e.text == 'Labels':
                State.show_labels = not State.show_labels
            elif e.text == 'Quit':
                quit()
