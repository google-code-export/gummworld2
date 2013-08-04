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


__doc__ = """29_basic_map_renderer.py - An example using the
BasicMapRenderer in Gummworld2.

The BasicMapRenderer provides a very easy way to scroll the background
tiles. It is as easy to use as the toolkit, and in most cases requires far
less memory than collapsing a map, without sacrificing high performance.
"""


import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import context, State, Engine, BasicMapRenderer
from gummworld2 import Statf, Vec2d, toolkit


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
        tile_size = 32,24
        map_size = 100,100
        
        self.movex = 0
        self.movey = 0
        
        Engine.__init__(self,
            resolution=screen_size,
            tile_size=tile_size, map_size=map_size,
            camera_target=CameraTarget(screen_size//2),
            frame_speed=0)
        
        self.scroll_speed = 10
        
        if __debug__: print 'App: making tiles'
        toolkit.make_tiles(label=True)
        
        if __debug__: print 'App: making renderer'
        self.renderer = BasicMapRenderer(
            State.map, max_scroll_speed=self.scroll_speed)
        
        if __debug__: print 'App: making HUD'
        toolkit.make_hud()
        next_pos = State.hud.next_pos
        State.hud.add('BasicMap tiles: ', Statf(next_pos(),
            'BasicMap tiles %d', callback=self._count_map_tiles, interval=.2))
        State.hud.add('Renderer tiles: ', Statf(next_pos(),
            'Renderer tiles %d', callback=lambda:len(self.renderer._tiles), interval=.2))
        
        if __debug__: print 'App: running'
    
    def _count_map_tiles(self):
        basic_map = State.map
        ids = toolkit.get_visible_cell_ids(
            State.camera, basic_map, self.scroll_speed)
        layers = toolkit.get_objects_in_cell_ids(basic_map, ids)
        count = 0
        for layer in layers:
            count += len(layer)
        return count
    
    def update(self, dt):
        if self.movex or self.movey:
            State.camera.position += self.movex,self.movey
        State.camera.update()
        self.renderer.set_rect(center=State.camera.rect.center)
        State.hud.update(dt)
    
    def draw(self, dt):
        State.screen.clear()
        self.renderer.draw_tiles()
        State.hud.draw()
        State.screen.flip()

    def on_key_down(self, unicode, key, mod):
        if key == K_DOWN: self.movey += self.scroll_speed
        elif key == K_UP: self.movey += -self.scroll_speed
        elif key == K_RIGHT: self.movex += self.scroll_speed
        elif key == K_LEFT: self.movex += -self.scroll_speed
        elif key == K_ESCAPE: context.pop()
    
    def on_key_up(self, key, mod):
        if key == K_DOWN: self.movey -= self.scroll_speed
        elif key == K_UP: self.movey -= -self.scroll_speed
        elif key == K_RIGHT: self.movex -= self.scroll_speed
        elif key == K_LEFT: self.movex -= -self.scroll_speed
    
    def on_quit(self):
        context.pop()


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
