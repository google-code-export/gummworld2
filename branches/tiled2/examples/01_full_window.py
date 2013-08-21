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


__doc__ = """01_full_window.py - An example of a full-window view for Gummworld2.
"""


import pygame
from pygame.locals import K_ESCAPE, K_UP, K_DOWN, K_LEFT, K_RIGHT

import paths
import gummworld2
from gummworld2 import context, Engine, State, toolkit


class App(Engine):
    
    def __init__(self):
        
        Engine.__init__(self,
            caption='01 Full Window',
            resolution=(600,600),
            tile_size=(128,128), map_size=(10,10),
            frame_speed=0)
        
        # Make some default content.
        toolkit.make_tiles()
        
        # Hold cursor key-down states.
        self.move_x = 0
        self.move_y = 0
        
    def update(self, dt):
        """overrides Engine.update"""
        self.update_camera_position()
        State.camera.update()

    def update_camera_position(self):
        """update the camera's position if any movement keys are held down
        """
        if self.move_y or self.move_x:
            camera = State.camera
            wx,wy = camera.position + (self.move_x,self.move_y)
            rect = State.world.rect
            wx = max(min(wx,rect.right), rect.left)
            wy = max(min(wy,rect.bottom), rect.top)
            camera.position = wx,wy
        
    def draw(self, interp):
        """overrides Engine.draw"""
        # Draw stuff.
        State.screen.clear()
        toolkit.draw_tiles()
        State.screen.flip()
        
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        if key == K_DOWN:
            self.move_y = 1 * State.speed
        elif key == K_UP:
            self.move_y = -1 * State.speed
        elif key == K_RIGHT:
            self.move_x = 1 * State.speed
        elif key == K_LEFT:
            self.move_x = -1 * State.speed
        elif key == K_ESCAPE:
            context.pop()
        
    def on_key_up(self, key, mod):
        # Turn off key-presses.
        if key in (K_DOWN,K_UP):
            self.move_y = 0
        elif key in (K_RIGHT,K_LEFT):
            self.move_x = 0
        
    def on_quit(self):
        context.pop()


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
