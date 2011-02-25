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


__doc__ = """00_minimum.py - The barest minimum to use a scrolling map in
Gummworld2.
"""


import pygame
from pygame.locals import *

import paths
from gummworld2 import State, Screen, Camera, GameClock, Map, Vec2d, toolkit


class CameraTarget(object):
    
    def __init__(self, position=(0,0)):
        self._position = Vec2d(position)
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        p = self._position
        p.x,p.y = val


class App(object):
    
    def __init__(self):
        
        tile_size = 128,128
        map_size = 10,10
        
        self.speed = 5
        self.movex = 0
        self.movey = 0
        
        ## Set up the State variables and load some map content.
        
        State.screen = Screen((800,600))
        State.map = Map(tile_size, map_size)
        camera_target = CameraTarget(State.screen.center)
        State.camera = Camera(camera_target)
        State.clock = GameClock(30, 0)
        
        toolkit.make_tiles()
    
    def run(self):
        ## Use the clock with a proper update/draw loop.
        while 1:
            State.clock.tick()
            if State.clock.update_ready():
                self.update()
            if State.clock.frame_ready():
                self.draw()

    def update(self):
        ## For each update cycle, update your game info and then the camera.
        self.get_events()
        self.update_camera()
    
    def update_camera(self):
        if self.movex or self.movey:
            State.camera.position += self.movex,self.movey
        State.camera.update()
    
    def draw(self):
        ## For each frame cycle, update the camera's interpolation and then draw
        ## the screen contents.
        
        State.camera.interpolate()
        
        State.screen.clear()
        toolkit.draw_tiles()
        State.screen.flip()

    def get_events(self):
        for e in pygame.event.get():
            if e.type == KEYDOWN:
                if e.key == K_DOWN: self.movey += self.speed
                elif e.key == K_UP: self.movey += -self.speed
                elif e.key == K_RIGHT: self.movex += self.speed
                elif e.key == K_LEFT: self.movex += -self.speed
                elif e.key == K_ESCAPE: quit()
            elif e.type == KEYUP:
                if e.key == K_DOWN: self.movey -= self.speed
                elif e.key == K_UP: self.movey -= -self.speed
                elif e.key == K_RIGHT: self.movex -= self.speed
                elif e.key == K_LEFT: self.movex -= -self.speed
            elif e.type == QUIT:
                quit()


if __name__ == '__main__':
    app = App()
    app.run()
