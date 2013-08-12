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


__doc__ = """basicmaprenderer.py - Basic Map Renderer module for Gummworld2.

Defines the BasicMapRenderer, which serves an intermediate batch of tiles
for efficient rendering. This class is intended to be used instead of
BasicMap's collapse() function. The renderer is compatible with a collapsed
map; it is simply offered as a replacement that is significantly less arcane
to use.

There is only a minor tradeoff in performance, even when a high number of
small tiles are in view.

The class attribute DEFAULT_LIFESPAN is the number of checks to perform
before retiring a tile that has not been displayed recently. Consider this a
crudely tunable garbage collector.

Here is an example game loop:
    
    def update(self, dt):
        if self.movex or self.movey:
            State.camera.position += self.movex,self.movey
        State.camera.update()
        self.renderer.set_rect(center=State.camera.rect.center)
    
    def draw(self, dt):
        State.screen.clear()
        self.renderer.draw_tiles()
        State.screen.flip()

If an occasional black band appears at the edge of the display while 
scrolling, increase the value of max_scroll_speed to the value of the
largest step (x or y) in use. This value can be changed situationally,
on the fly, without significant overhead.
"""


import pygame
from pygame.locals import *

from gummworld2 import State, BasicMap


class BasicMapRenderer(object):
    
    DEFAULT_LIFESPAN = 30 * 2  ## ticks * calls to get_tiles()
    
    _allowed_rect = (
        'x','y','left','right','top','bottom',
        'center','midleft','midright','midtop','midbottom',
        'topleft','topright','bottomleft','bottomright',
    )
    
    def __init__(self, basic_map, tile_size=0, max_scroll_speed=10):
        self._basic_map = basic_map
        self._rect = Rect(State.screen.rect)
        self._max_scroll_speed = max_scroll_speed
        
        self._tiles = {}
        self._visible_tiles = []
        
        self._view_count = 0
        self._lifespan = self.DEFAULT_LIFESPAN
        self._examine_queue = []
        self._dead = []
        self.dirty_rects = []
        
        self.tile_size = tile_size
        
        self.get_tiles()
    
    def get_rect(self):
        return Rect(self._rect)
    def set_rect(self, **kwargs):
        """set the world location of the renderer's view rect"""
        ## may be an opportunity here for a memoization performance gain to
        ## keep tiles if the move does not select a new region
        del self._visible_tiles[:]
        for k in kwargs:
            if k not in self._allowed_rect:
                raise pygame.error('rect attribute not permitted: %s' % (k,))
            setattr(self._rect, k, kwargs[k])
        self.get_tiles()
        del self.dirty_rects[:]
    
    @property
    def max_scroll_speed(self):
        return self._max_scroll_speed
    @max_scroll_speed.setter
    def max_scroll_speed(self, val):
        assert isinstance(val, int)
        self._max_scroll_speed = val
    @property
    def lifespan(self):
        return self._lifespan
    @lifespan.setter
    def lifespan(self, val):
        """set a new lifespan on tiles"""
        self._lifespan = val
    @property
    def tile_size(self):
        return self._tile_size
    @tile_size.setter
    def tile_size(self, val):
        """set a new tile size"""
        assert isinstance(val, int)
        if val <= 0:
            val = self._rect.width / 4
        self._tile_size = val
        self._clear()
        self.get_tiles()
    @property
    def basic_map(self):
        return self._basic_map
    @basic_map.setter
    def basic_map(self, val):
        """register a new BasicMap"""
        assert isinstance(val, BasicMap)
        self._basic_map = val
        self._clear()
        self.get_tiles()
    
    def set_dirty(self, *areas):
        """specify areas to re-render
        
        The areas argument must be one or more pygame.Rect.
        
        Marking areas dirty is necessary only if the underlying BasicMap
        tiles are procedurally modified during runtime. Though it involves
        some management, it is potentially much more efficient than
        triggering the entire view be recreated.
        """
        tiles = self._tiles
        for rect in areas:
            for tile in tiles.values():
                if rect.colliderect(tile.rect):
                    self.dirty_rects.append(tile.rect)
                    del tiles[tile.idx]
        self.get_tiles()
    
    def get_tiles(self):
        """call once per tick to calculate visible tiles
        
        The constructor does this automatically, and it is done each time
        set_rect() is called. It may be necessary to call get_tiles()
        manually depending on the implementation; for example, if the
        renderer object is created before the map is loaded.
        """
        visible_tiles = self._visible_tiles
        if visible_tiles:
            return visible_tiles
        
        self._view_count += 1
        self._age_tiles()
        stamp = self._view_count
        
        speed = self._max_scroll_speed * 2
        X,Y,W,H = self._rect.inflate(speed, speed)[:]
        SIZE = self._tile_size
        X = X / SIZE * SIZE
        Y = Y / SIZE * SIZE
        TILES = self._tiles
        get_tile = TILES.get
        for x in xrange(X, X+W+SIZE, SIZE):
            for y in xrange(Y, Y+H+SIZE, SIZE):
                idx = (x,y)
                if idx not in TILES:
                    tile = BasicMapRendererTile(idx, SIZE, self)
                    TILES[idx] = tile
                else:
                    tile = get_tile(idx)
                tile.stamp = stamp
                visible_tiles.append(tile)
    
    def draw_tiles(self):
        """draw the visible tiles on the screen"""
        self._rect.center = State.camera.rect.center
        screen = State.screen
        blit = screen.surface.blit
        view_rect = self._rect
        colliderect = view_rect.colliderect
        x,y = view_rect.topleft
        for tile in self._visible_tiles:
            r = tile.rect
            if colliderect(r):
                blit(tile.image, r.move(-x, -y))
    
    def _age_tiles(self):
        """weed out aged tiles nicely"""
        queue = self._examine_queue
        tiles = self._tiles
        if not queue:
            queue[:] = tiles.values()
        stamp = self._view_count
        dead = self._dead
        lifespan = self._lifespan
        i = 0
        while queue:
            i += 1
            if i > 30:
                # performance throttle: only do 30 per check
                break
            tile = queue.pop(0)
            if stamp - tile.stamp > lifespan:
                dead.append(tile)
        for tile in dead:
            try:
                del tiles[tile.idx]
            except KeyError:
                pass
        del dead[:]
    
    def _clear(self):
        """clear all tile caches"""
        self._tiles.clear()
        del self._visible_tiles[:]
        del self._examine_queue[:]
        del self._dead[:]


class BasicMapRendererTile(object):
    
    def __init__(self, idx, size, renderer):
        self.idx = idx
        self.renderer = renderer
        dim = (size,size)
        self.image = pygame.Surface(dim)
        self.rect = self.image.get_rect(topleft=idx, size=dim)
        
        blit = self.image.blit
        x,y = idx
        
        map_ = State.map
        camera = State.camera
        cx,cy = self.rect.topleft
        visible_cell_ids = _get_visible_cell_ids(camera, map_, self.rect)
        visible_objects = _get_objects_in_cell_ids(map_, visible_cell_ids)
        for sprites in visible_objects:
            for sprite in sprites:
                rect = sprite.rect
                sx,sy = rect.topleft
                blit(sprite.image, (sx-cx,sy-cy))


# The following functions
#   _get_visible_cell_ids
#   _get_objects_in_cell_ids
# are similar to the functions of the same name in gummworld2.toolkit,
# except that they operate on a query_rect instead of the camera.
#
# These functions assist a BasicMapRendererTile in constructing itself.

def _get_visible_cell_ids(camera, map_, query_rect):  #, max_speed=10):
    empty_list = []
    cell_ids = []
#    query_rect = query_rect.inflate(max_speed*2,max_speed*2)
    for layer in map_.layers:
        if layer.visible:
            cell_ids.append(layer.objects.intersect_indices(query_rect))
        else:
            cell_ids.append(empty_list)
    return cell_ids


def _get_objects_in_cell_ids(map_, cell_ids_per_layer):
    objects_per_layer = []
    for layeri,cell_ids in enumerate(cell_ids_per_layer):
        get_cell = map_.layers[layeri].objects.get_cell
        objects = set()
        objects_update = objects.update
        for cell_id in cell_ids:
            objects_update(get_cell(cell_id))
        objects_per_layer.append(list(objects))
    return objects_per_layer
