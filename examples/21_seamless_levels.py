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


__doc__ = """21_seamless_levels.py - Connecting levels in Gummworld2.


NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE NOTE 

To see how it is intended to look, take a look at 19_parallax.py. Demo 19 uses
one map, whereas this one attempts to link two maps seamlessly in realtime.

Parallax rendering is working in this demo, but the seamless part is not.

"""


from random import randrange

import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import context, model, toolkit
from gummworld2 import State, Engine, Map, MapLayer, View, Vec2d


class Level(Engine):
    ## This just holds a map and a camera for tile processing. It was originally
    ## intended to be a context; exchanging contexts triggers State to be
    ## modified. But that behavior may no longer be needed: the experiment
    ## parallax functions take camera and map arguments and do their own
    ## tile-picking.
    
    def __init__(self, rect):
        
        tile_size = Vec2d(256,256)
        map_size = Vec2d(8,3)
        
        # Position and size the memory rect, then create a map and set its
        # position.
        rect.left = rect.right
        rect.size = map_size * tile_size
        
        map = Map(tile_size, map_size)
        map.rect.center = rect.center
        
        Engine.__init__(self,
            map=map,                        # use my pre-made map
            default_schedules=False,        # don't schedule world and camera
            set_state=False,                # enter/resume doesn't modify State
        )
        self.view = State.screen
        self.camera = None
        self.clock = None
        self.set_state()
        
        self.make_map()
        
        self.test_rect = Rect(State.camera.rect)
        
    def update(self, dt):
        """override"""
        pass


class Level0(Level):
    
    def update(self, dt, move):
        if move:
            test_rect = self.test_rect
            world_rect = self.world.rect
            test_rect.center = State.camera.rect.center + move
            if test_rect.left < 0:
                test_rect.left = 0
            if test_rect.top < world_rect.top:
                test_rect.top = world_rect.top
            elif test_rect.bottom > world_rect.bottom:
                test_rect.bottom = world_rect.bottom
            State.camera.position = self.test_rect.center
    
    def make_map(self):
        make_map(self.map, moon=True)


class Level1(Level):
    
    def update(self, dt, move):
        if move:
            test_rect = self.test_rect
            world_rect = self.world.rect
            test_rect.center = State.camera.rect.center + move
            if test_rect.right > world_rect.right:
                test_rect.right = world_rect.right
            if test_rect.top < world_rect.top:
                test_rect.top = world_rect.top
            elif test_rect.bottom > world_rect.bottom:
                test_rect.bottom = world_rect.bottom
            State.camera.position = test_rect.center
    
    def make_map(self):
        make_map(self.map)


class LevelManager(Engine):
    
    def __init__(self):
        
        ## changing screen size messes with parallax rendering
        screen_size = Vec2d(320,512)
        ##screen_size = Vec2d(300,300)
        
        Engine.__init__(self,
            resolution=screen_size,
            camera_target=model.Object(),
            frame_speed=30)
        rect = pygame.Rect(-1,0,1,1)
        self.levels = [Level0(rect), Level1(rect)]
        self.current = 0        # current "primary" level has draw precedence
        self.on_screen = []     # levels that are on screen
        self.cam_rects = {}     # camera rect for each layer
        self.tiles = {}         # tiles for each layer
        
        self.levels[0].set_state()
        State.clock.update_callback = self.update
        State.clock.frame_callback = self.draw
        
        mx = State.map.rect.centerx
        my = State.map.rect.h * 2/3
        State.camera.init_position((mx,my))
        
        self.move = Vec2d(0,0)
        State.speed = 10
        
        self.hit_rect = self.screen.rect.inflate(State.speed,State.speed)
        
        self.set_state()
        self.update(0)
        
        State.clock.schedule_interval(self.set_caption, 2.)
    
    def set_caption(self, dt):
        pygame.display.set_caption('21 Seamless - %d fps | Current: %d' % (
            State.clock.fps, self.current))
    
    def update(self, dt):
        current = self.current
        levels = self.levels
        level = levels[current]
        level.set_state()
        cam = State.camera
        level.update(dt, self.move)
        # Switch current level if we've moved beyond its bounds.
        if not level.world.rect.collidepoint(State.camera.position):
            for i,level in enumerate(levels):
                if level.world.rect.collidepoint(State.camera.position):
                    self.current = current = i
                    break
        # If screen is straddling levels, add the other level to render.
        CAM_RECT = State.camera.rect
        del self.on_screen[:]
        self.hit_rect.center = CAM_RECT.center
        for level in self.levels:
            if self.hit_rect.colliderect(level.map.rect):
                self.on_screen.append(level)
#        print self.on_screen
        # Build the tile list to render.
        self.cam_rects.clear()
        self.tiles.clear()
        for level in self.on_screen:
            map = level.map
            layers = map.layers
            for layeri,layer in enumerate(layers):
                parallax = layer.parallax
                (x1,y1,x2,y2),cam_rect = toolkit.get_parallax_tile_range(
                    State.camera, map, layer, parallax)
                # Save the tiles and camera rects used to render the tiles.
                KEY = level,layeri
                self.cam_rects[KEY] = cam_rect
                if KEY not in self.tiles: self.tiles[KEY] = []
                # A tile can be None. Filter them.
                self.tiles[KEY].extend(
                    [t for t in map.get_tiles(x1,y1,x2,y2, layeri) if t])
        if len(self.on_screen) > 1:
            # We have two visible levels. Make an exclusive subsurface for each
            # to control tile "spillover".
            #
            # We want to use the 1.0 layer (no parallax factor) to define our
            # bounding rect for drawing tiles.
            screen_rect = State.screen.rect
            camera = State.camera
            cam_rect = camera.rect
            w2s = camera.world_to_screen
            for leveli,level in enumerate(list(self.on_screen)):
                map_rect = level.map.rect
                x,y = w2s(map_rect.topleft)
                if x < screen_rect.x: x = screen_rect.x
                if y < screen_rect.y: y = screen_rect.y
                right,bottom = w2s(map_rect.bottomright)
                if right > screen_rect.right: right = screen_rect.right
                if bottom > screen_rect.bottom: bottom = screen_rect.bottom
                w = right - x
                h = bottom - y
                if w < 0 or h < 0:
                    del self.on_screen[leveli]
                else:
                    r = Rect(x,y,w,h)
                    level.view = View(subsurface_rect=r)
        else:
            # Use full screen.
            self.on_screen[0].view = State.screen
    
    def draw(self, dt):
        State.camera.interpolate()
        State.screen.clear()
        for level in self.on_screen:
            layers = level.map.layers
            for layeri,layer in enumerate(layers):
                KEY = level,layeri
                tiles = self.tiles[KEY]
                cam_rect = self.cam_rects[KEY]
                view = level.view
                toolkit.draw_parallax_tiles(layer, tiles, cam_rect, view)
        State.screen.flip()
    
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


def sprite_sort_key(self):
    # self.name is a tuple representing the x,y grid position of the tile in
    # the map, e.g. (0,0), (1,0)...
    return self.name


def make_map(map, moon=False):
    primary_layer_only = False
    map = State.map
    tw,th = map.tile_size
    mw,mh = map.map_size
    ## Layer 0: Sky with stars.
    layer = MapLayer(map.tile_size, map.map_size, make_labels=True, make_grid=True)
    layer.parallax = Vec2d(.25,.25)
    for y in range(map.rect.top//th, map.rect.bottom//th):
        for x in range(map.rect.left//tw, map.rect.right//tw):
            sprite = pygame.sprite.Sprite()
            sprite.name = x,y
            sprite.image = pygame.surface.Surface((tw,th))
            sprite.rect = sprite.image.get_rect(topleft=(tw*x,th*y))
            for p in [(randrange(256),randrange(256)) for i in range(randrange(30,45))]:
                pygame.draw.line(sprite.image, Color('white'), p, p)
            layer.append(sprite)
    ## A great big moon.
    if moon:
        pygame.draw.circle(
            layer.get_tile_at(4,1).image, Color(255,255,170), (128,128), 75)
    if not primary_layer_only:
        map.layers.append(layer)
    ## Layer 1: Mountains.
    layer = MapLayer(map.tile_size, map.map_size, make_labels=True, make_grid=True)
    layer.parallax = Vec2d(.55,.55)
    skyline = [(0,th-randrange(randrange(100,150),th-1))]
    for y in range(map.rect.top//th, map.rect.bottom//th):
        for x in range(map.rect.left//tw, map.rect.right//tw):
            sprite = pygame.sprite.Sprite()
            sprite.name = x,y
            sprite.image = pygame.surface.Surface((tw,th))
            sprite.image.set_colorkey(Color('black'))
            sprite.sort_key = sprite_sort_key
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
            layer.append(sprite)
    if not primary_layer_only:
        map.layers.append(layer)
    ## Layer 2,3,4: Trees.
    tree_data = [
        # color         parallax      treetops numtrees
        (Color(0,16,0), Vec2d(.65,.65), th*8/16, 100),
        (Color(0,22,0), Vec2d(.8,.8), th*11/16,  75),
        (Color(0,33,0), Vec2d(1.,1.),   th*15/16, 50),
    ]
    make_grid = True
    make_labels = True
    for color,parallax,treetops,numtrees in tree_data:
        layer = MapLayer(map.tile_size, map.map_size, make_labels=True, make_grid=True)
        layer.parallax = parallax
        skyline = [(0,th-randrange(randrange(100,150),th-1))]
        for y in range(map.rect.top//th, map.rect.bottom//th):
            ox = []
            rx = []
            for x in range(map.rect.left//tw, map.rect.right//tw):
                # Null tile if it is "in the sky" and tile debugging is off.
                if y < mh-1 and not (make_grid or make_labels):
                    layer.append(None)
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
                layer.append(sprite)
        if not primary_layer_only:
            map.layers.append(layer)
        elif parallax == (1,1):
            map.layers.append(layer)


if __name__ == '__main__':
    level_manager = LevelManager()
    gummworld2.run(level_manager)
