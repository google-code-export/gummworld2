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
from gummworld2 import context, State, Engine, BasicLayer, Vec2d, toolkit


class App(Engine):
    
    def __init__(self):
        
        screen_size = Vec2d(512,512)
        ## BUG: Would be nice to have parallax layers line up properly when
        ## screen is scaled. To see the problem use the display size 300,300.
        ##screen_size = Vec2d(300,300)
        tile_size = 256,256
        map_size = 8,3
        
        self.move = Vec2d(0,0)
        
        Engine.__init__(self,
            resolution=screen_size,
            tile_size=tile_size, map_size=map_size,
            frame_speed=0)
        
        make_map()
        pos = State.map.rect.centerx, State.map.rect.height * 2//3
        State.camera.init_position(pos)
        self.test_rect = Rect(State.camera.rect)
        
        State.clock.schedule_interval(self.set_caption, 2.)
        State.speed = 10
        
        toolkit.make_hud()
    
    def set_caption(self, dt):
        pygame.display.set_caption('19 Parallax - %d fps' % State.clock.fps)
    
    def update(self, dt):
        if self.move:
            test_rect = self.test_rect
            test_rect.center += self.move
            test_rect.clamp_ip(State.map.rect)
            State.camera.position = test_rect.center
        State.camera.update(dt)
        State.hud.update(dt)
    
    def draw(self, dt):
        State.screen.clear()
        self.draw_tiles()
        State.hud.draw()
        State.screen.flip()
    
    def draw_tiles(self):
        draw = toolkit.draw_parallax_tiles_of_layer
        camera = State.camera
        map = State.map
        for layeri,layer in enumerate(State.map.layers):
            parallax = layer.parallax
            draw(camera, map, layer, parallax)
            #toolkit.draw_tiles_of_layer(layeri, parallax.x, parallax.y)
    
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
    tw,th = map.tile_width,map.tile_height
    mw,mh = map.width,map.height
    ## Layer 0: Sky with stars.
    layeri = 0
    layer = BasicLayer(map, layeri)
    layer.parallax = Vec2d(.25,.25)
    make_grid = False
    make_labels = False
    for y in range(mh):
        for x in range(mw):
            sprite = pygame.sprite.Sprite()
            sprite.name = x,y
            sprite.image = pygame.surface.Surface((tw,th))
            sprite.rect = sprite.image.get_rect(topleft=(tw*x,th*y))
            for p in [(randrange(256),randrange(256)) for i in range(randrange(30,45))]:
                pygame.draw.line(sprite.image, Color('white'), p, p)
            # Tile debugging.
            if make_labels:
                font = gummworld2.ui.hud_font
                tex = font.render(str(sprite.name), True, Color('yellow'))
                sprite.image.blit(tex, (1,1))
            if make_grid:
                pygame.draw.rect(sprite.image, Color('darkgrey'), sprite.image.get_rect(), 1)
            layer.add(sprite)
    ## A great big moon.
    x = 2 * layer.tile_width
    y = 1 * layer.tile_height
    moon_sprite = layer.objects.intersect_objects(Rect(x,y,1,1))[0]
    pygame.draw.circle(moon_sprite.image, Color(255,255,170), (128,128), 75)
    map.layers.append(layer)
    ## Layer 1: Mountains.
    layeri += 1
    layer = BasicLayer(map, layeri)
    layer.parallax = Vec2d(.55,.55)
    skyline = [(0,th-randrange(randrange(100,150),th-1))]
    for y in range(mh):
        for x in range(mw):
            sprite = pygame.sprite.Sprite()
            sprite.name = x,y
            sprite.image = pygame.surface.Surface((tw,th))
            sprite.image.set_colorkey(Color('black'))
            if y == mh-1:
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
            sprite.rect = sprite.image.get_rect(topleft=(tw*x,th*y))
            layer.add(sprite)
    map.layers.append(layer)
    ## Layer 2,3,4: Trees.
    tree_data = [
        # color         parallax      treetops numtrees
        (Color(0,16,0), Vec2d(.65,.65), th*8/16, 100),
        (Color(0,22,0), Vec2d(.8,.8), th*11/16,  75),
        (Color(0,33,0), Vec2d(1.,1.),   th*15/16, 50),
    ]
    make_grid = False
    make_labels = False
    for color,parallax,treetops,numtrees in tree_data:
        layeri += 1
        layer = BasicLayer(map, layeri)
        layer.parallax = parallax
        skyline = [(0,th-randrange(randrange(100,150),th-1))]
        for y in range(mh):
            ox = []
            rx = []
            for x in range(mw):
                # Null tile if it is "in the sky" and tile debugging is off.
                if y < mh-1 and not (make_grid or make_labels):
##                    layer.add(None)
                    continue
                sprite = pygame.sprite.Sprite()
                sprite.name = x,y
                sprite.image = pygame.surface.Surface((tw,th))
                sprite.image.set_colorkey(Color('black'))
                sprite.rect = sprite.image.get_rect(topleft=(tw*x,th*y))
                # Draw trees on ground tiles.
                if y == mh-1:
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
                # Tile debugging.
                if make_labels:
                    font = gummworld2.ui.hud_font
                    tex = font.render(str(sprite.name), True, Color('yellow'))
                    sprite.image.blit(tex, (1,1))
                if make_grid:
                    pygame.draw.rect(sprite.image, color, sprite.image.get_rect(), 1)
                layer.add(sprite)
        map.layers.append(layer)


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
