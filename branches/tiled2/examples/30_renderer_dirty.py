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


__doc__ = """30_renderer_dirty.py - An example of modifying the map in realtime with
the renderer in Gummworld2.
"""


import random

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
        map_size = 25,25
        
        self.movex = 0
        self.movey = 0
        
        Engine.__init__(self,
            caption='30 Renderer Dirty - Num picks: +/-',
            resolution=screen_size,
            tile_size=tile_size, map_size=map_size,
            camera_target=CameraTarget(screen_size//2),
            frame_speed=0)
        
        self.scroll_speed = 4
        
        toolkit.make_tiles(label=True)
        self.fill_color = Color(50,50,50)
        self.frame_color = Color(0,0,0)
        self.dirty_color = Color(100,50,50)
        for tile in self.map.layers[0].objects.objects:
            self._color_image(
                tile.image, self.fill_color, self.frame_color)
        
        self.renderer = BasicMapRenderer(
            State.map, max_scroll_speed=self.scroll_speed)
        self.num_picks = 1
        self.picks = []
        self._pick_tiles()
        
        toolkit.make_hud()
        next_pos = State.hud.next_pos
        State.hud.add('BasicMap tiles', Statf(next_pos(),
            'BasicMap tiles %d', callback=self._count_map_tiles, interval=.2))
        State.hud.add('Renderer tiles', Statf(next_pos(),
            'Renderer tiles %d', callback=lambda:len(self.renderer._tiles), interval=.2))
        State.hud.add('Num picks', Statf(next_pos(),
            'Num picks %d', callback=lambda:self.num_picks, interval=.2))
        State.hud.add('Dirty rects', Statf(next_pos(),
            'Dirty rects %d', callback=lambda:len(self.renderer.dirty_rects), interval=.2))
        
        self.clock.schedule_interval(self._pick_tiles, 2.0)
    
    def update(self, dt):
        if self.movex or self.movey:
            State.camera.position += self.movex,self.movey
        State.camera.update()
        self.renderer.set_rect(center=State.camera.rect.center)
        self._update_tiles()
        State.hud.update(dt)
    
    def _update_tiles(self):
        """modify tile picks"""
        self._up_dirty_color()
        color = self.dirty_color
        for tile in self.picks:
            self._color_image(tile.image, color, self.frame_color)
            self.renderer.set_dirty(tile.rect)
    
    def _up_dirty_color(self):
        """bump color up in brightness"""
        color = self.dirty_color
        if color.r < 253:
            color.r += 2
            color.g += 1
            color.b += 1
    
    def _color_image(self, image, fill_color, frame_color):
        """apply color to an image"""
        image.fill(fill_color)
        pygame.draw.rect(image, frame_color, image.get_rect(), 1)
    
    def _pick_tiles(self, *args):
        """pick random tiles to modify"""
        self.dirty_color.r = 100
        self.dirty_color.g = 50
        self.dirty_color.b = 50
        for tile in self.picks:
            self._color_image(tile.image, self.fill_color, self.frame_color)
        del self.picks[:]
        for i in xrange(self.num_picks):
            self.picks.append(random.choice(self.map.layers[0].objects.objects))
    
    def _add_pick(self):
        """add a tile pick"""
        self.num_picks += 1
        self.picks.append(random.choice(self.map.layers[0].objects.objects))
    
    def _remove_pick(self):
        """remove a tile pick"""
        if len(self.picks) > 1:
            self.num_picks -= 1
            self.picks.pop(0)
    
    def _count_map_tiles(self):
        """count tiles in map for the HUD"""
        basic_map = State.map
        ids = toolkit.get_visible_cell_ids(
            State.camera, basic_map, self.scroll_speed)
        layers = toolkit.get_objects_in_cell_ids(basic_map, ids)
        count = 0
        for layer in layers:
            count += len(layer)
        return count
    
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
        elif key in (K_EQUALS,K_PLUS): self._add_pick()
        elif key == K_MINUS: self._remove_pick()
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
