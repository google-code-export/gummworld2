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


__version__ = '0.2'
__vernum__ = (0,2)


"""map.py - Map module for Gummworld2.

Defines the Map, which serves tiles, tile labels, and grid outlines. Supports
tile layers.

Map combines view (pygame) and model (world coordinates). It contains a rect
attribute defining its dimensions, and observes pygame coordinate space.

The caller must manage maps and their corresponding worlds by swapping the
State.map and State.world package globals, for example:
    
    # Create the initial map and world, and save it.
    State.map = Map(tile_size, map_size)
    State.world = model.World(State.map.rect)
    levels = []
    levels.append((State.map,State.world))
    ...
    # Create a new one, save it.
    State.map = Map(new_tile_size, new_map_size)
    State.world = model.World(State.map.rect)
    levels.append((State.map,State.world))
    ...
    # Restore a map and world.
    State.map,State.world = levels[0]
    
Alternatively State.save() and State.restore() can be used to facilitate this.
"""


import pygame
from pygame.locals import Color

from gamelib import data, model, State, Vec2d
from gamelib.ui import text_color


class Map(object):
    
    def __init__(self, tile_size, map_size):
        self.tile_size = Vec2d(tile_size)
        self.map_size = Vec2d(map_size)
        self.layers = []
        self.visible = []
        
        tw,th = tile_size
        mw,mh = map_size
        self.rect = pygame.Rect(0,0,tw*mw,th*mh)
        
        # make a tile outline to blit for optional grid
        s = pygame.sprite.Sprite()
        s.image = pygame.surface.Surface((tw,th))
        s.rect = s.image.get_rect()
        pygame.draw.rect(s.image, Color('white'), s.rect, 1)
        s.image.set_colorkey(Color('black'))
        s.image.set_alpha(25)
        self.outline = s
        
        # make grid labels to blit
        self.labels = {}
        font = pygame.font.Font(data.filepath('font', 'Vera.ttf'), 8)
        for x in range(0,mw):
            for y in range(0,mh):
                s = pygame.sprite.Sprite()
                s.image = font.render('%d,%d'%(x,y), True, text_color)
                s.rect = s.image.get_rect(
                    topleft=Vec2d(x*tw,y*th)+(2,2))
                self.labels[x,y] = s
    
    def add(self, *tiles, **kwargs):
        """Map.add(*tiles, layer=0)
        """
        layer = kwargs.get('layer', 0)
        for s in tiles:
            if not isinstance(s, pygame.sprite.Sprite):
                raise pygame.error, '*tiles argument must be one or more sprites'
            if not isinstance(s.name, tuple):
                raise pygame.error, 'name property must be an (x,y) tuple'
            self.layers[layer][s.name] = s
    
    def clear(self):
        del self.layers[:]
    
    def remove(self, x, y, layer=0):
        tile = self.get_tile_at(x, y, layer=layer)
        del self.layers[layer][x,y]
        return tile
    
    def get_tile_at(self, x, y, layer=0):
        return self.layers[layer].get((x,y), (None,(x,y)))

    def get_tiles(self, x1, y1, x2, y2, layer=0):
        """Map.get_tiles(self, x1, y1, x2, y2, layer=0) : list
        
        x1,y1,x2,y2 -> int; Range of tiles to select.
        layer -> int; Tile layer to select.
        
        Return the list of tiles at the specified layer in range (x1,y1)
        through (x2,y2). If the layer is not visible, an empty list is returned.
        """
        if self.layers[layer].visible:
            return [self.layers[layer].get((x,y), (None,(x,y)))
                for x in xrange(x1,x2)
                    for y in xrange(y1,y2)]
        else:
            return []

    def get_label_at(self, x, y):
        return self.labels.get((x,y), (None,(x,y)))
    
    def get_labels(self, x1, y1, x2, y2):
        return [self.labels.get((x,y), (None,(x,y)))
            for x in xrange(x1,x2)
                for y in xrange(y1,y2)]
    
    def vertical_grid_line(self, xy=None, anchor='topleft'):
        if xy is not None:
            setattr(self.v_line, anchor, xy)
        return self.v_line
    
    def horizontal_grid_line(self, xy=None, anchor='topleft'):
        if xy is not None:
            setattr(self.h_line, anchor, xy)
        return self.h_line


class MapLayer(dict):
    
    def __init__(self, visible=True):
        super(MapLayer, self).__init__()
        self.visible = visible
