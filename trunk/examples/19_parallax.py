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


__doc__ = """19_parallax.py - Using map layers to produce the illusion of
parallax in Gummworld2.
"""


from random import randrange

import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import context, State, Engine, MapLayer, Vec2d, toolkit


class App(Engine):
    
    def __init__(self):
        
        screen_size = Vec2d(512,512)
        tile_size = 256,256
        map_size = 8,3
        
        self.move = Vec2d(0,0)
        
        Engine.__init__(self,
            resolution=screen_size,
            tile_size=tile_size, map_size=map_size,
            frame_speed=0)
        
        make_map()
        mx = State.map.rect.centerx
        my = State.map.rect.h * 2/3
        State.camera.init_position((mx,my))
        
        self.test_rect = Rect(State.camera.rect)
        
        State.clock.schedule_interval(self.set_caption, 2.)
    
    def set_caption(self, dt):
        pygame.display.set_caption('19 Parallax - %d fps' % State.clock.fps)
    
    def update(self, dt):
        if self.move:
            self.test_rect.center += self.move
            self.test_rect.clamp_ip(State.map.rect)
            State.camera.position = self.test_rect.center
    
    def draw(self, dt):
        State.screen.clear()
        self.draw_tiles()
        State.screen.flip()
    
    def draw_tiles(self):
        for layeri,layer in enumerate(State.map.layers):
            parallax = layer.parallax
            toolkit.draw_tiles_of_layer(layeri, parallax.x, parallax.y)
    
    def on_key_down(self, unicode, key, mod):
        if key == K_DOWN: self.move.y += State.speed
        elif key == K_UP: self.move.y += -State.speed
        elif key == K_RIGHT: self.move.x += State.speed
        elif key == K_LEFT: self.move.x += -State.speed
        elif key == K_ESCAPE: context.pop()
    
    def on_key_up(self, key, mod):
        if key == K_DOWN: self.move.y -= State.speed
        elif key == K_UP: self.move.y -= -State.speed
        elif key == K_RIGHT: self.move.x -= State.speed
        elif key == K_LEFT: self.move.x -= -State.speed
    
    def on_quit(self):
        context.pop()


def make_map():
    map = State.map
    tw,th = map.tile_size
    mw,mh = map.map_size
    ## Layer 0: Sky with stars.
    layer = MapLayer(map.tile_size, map.map_size)
    layer.parallax = Vec2d(.25,.25)
    for y in range(mh):
        for x in range(mw):
            sprite = pygame.sprite.Sprite()
            sprite.name = (tw*x,th*y)
            sprite.image = pygame.surface.Surface((tw,th))
            sprite.rect = sprite.image.get_rect(topleft=sprite.name)
            for p in [(randrange(256),randrange(256)) for i in range(randrange(30,45))]:
                pygame.draw.line(sprite.image, Color('white'), p, p)
            layer.append(sprite)
    ## A great big moon.
    pygame.draw.circle(layer.get_tile_at(2,0).image, Color(255,255,170), (128,128), 75)
    map.layers.append(layer)
    ## Layer 1: Mountains.
    layer = MapLayer(map.tile_size, map.map_size)
    layer.parallax = Vec2d(.55,.55)
    skyline = [(0,th-randrange(randrange(100,150),th-1))]
    y = mh - 1
    for x in range(mw):
        sprite = pygame.sprite.Sprite()
        sprite.name = (tw*x,th*y)
        sprite.image = pygame.surface.Surface((tw,th))
        sprite.image.set_colorkey(Color('black'))
        sprite.rect = sprite.image.get_rect(topleft=sprite.name)
        skyline = [(tw-1,th-1), (0,th-1), (0,skyline[-1][1])]
        vertices = randrange(3,5)
        points = []
        for i in range(0,tw+1,tw/vertices):
            i += randrange(25,75)
            if i >= tw: i = tw - 1
            points.append((i,th-randrange(randrange(150,th-1),th-1)))
            if i == tw - 1: break
        points.sort()
        skyline.extend(points)
        pygame.draw.polygon(sprite.image, Color(18,5,5), skyline)
        pygame.draw.lines(sprite.image, Color(25,22,18), False, skyline[2:], 6)
        layer.append(sprite)
    map.layers.append(layer)
    ## Layer 2,3,4: Trees.
    tree_data = [
        # color         parallax      treetops numtrees
        (Color(0,16,0), Vec2d(.65,.65), th*8/16, 100),
        (Color(0,22,0), Vec2d(.8,.8), th*11/16,  75),
        (Color(0,33,0), Vec2d(1.,1.),   th*15/16, 50),
    ]
    for color,parallax,treetops,numtrees in tree_data:
        layer = MapLayer(map.tile_size, map.map_size)
        layer.parallax = parallax
        skyline = [(0,th-randrange(randrange(100,150),th-1))]
        y = mh - 1
        ox = []
        rx = []
        for x in range(mw):
            sprite = pygame.sprite.Sprite()
            sprite.name = (tw*x,th*y)
            sprite.image = pygame.surface.Surface((tw,th))
            sprite.image.set_colorkey(Color('black'))
            sprite.rect = sprite.image.get_rect(topleft=sprite.name)
            for i,o in enumerate(ox):
                pygame.draw.circle(sprite.image, color, o, rx[i])
            del ox[:],rx[:]
            for i in range(numtrees):
                r = randrange(25,35)
                o = randrange(r,tw), randrange(treetops,th)
                pygame.draw.circle(sprite.image, color, o, r)
                if o[0]+r >= tw:
                    ox.append((o[0]-tw, o[1]))
                    rx.append(r)
            layer.append(sprite)
        map.layers.append(layer)


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
