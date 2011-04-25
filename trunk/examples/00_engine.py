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


__doc__ = """00_engine.py - The barest minimum to use the scrolling map engine
in Gummworld2.
"""


import pygame
from pygame.locals import *

import paths
from gummworld2 import State, Engine, Vec2d, toolkit


class CameraTarget(object):
    
    def __init__(self, position=(0,0)):
        self._position = Vec2d(position)
    
    ## A camera target just needs to have a Vec2d position attribute. It helps
    ## to protect it from overwriting with other types.
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        self._position[:] = val


class App(Engine):
    
    def __init__(self):
        
        screen_size = Vec2d(800,600)
        tile_size = 128,128
        map_size = 10,10
        
        self.movex = 0
        self.movey = 0
        
        ## Set up the State variables and load some map content.
        
        Engine.__init__(self,
            resolution=screen_size,
            camera_target=CameraTarget(screen_size//2),
            frame_speed=0)
        
        toolkit.make_tiles()
    
    def update(self, dt):
        ## For each update cycle, update your game info and camera.
        if self.movex or self.movey:
            State.camera.position += self.movex,self.movey
    
    def draw(self, dt):
        ## For each frame cycle, draw the screen contents.
        State.screen.clear()
        toolkit.draw_tiles()
        State.screen.flip()

    def on_key_down(self, unicode, key, mod):
        if key == K_DOWN: self.movey += State.speed
        elif key == K_UP: self.movey += -State.speed
        elif key == K_RIGHT: self.movex += State.speed
        elif key == K_LEFT: self.movex += -State.speed
        elif key == K_ESCAPE: quit()
    
    def on_key_up(self, key, mod):
        if key == K_DOWN: self.movey -= State.speed
        elif key == K_UP: self.movey -= -State.speed
        elif key == K_RIGHT: self.movex -= State.speed
        elif key == K_LEFT: self.movex -= -State.speed
    
    def on_quit(self):
        quit()


if __name__ == '__main__':
    app = App()
    app.run()
