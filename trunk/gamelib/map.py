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


__version__ = '0.3'
__vernum__ = (0,3)


__doc__ = """map.py - Map module for Gummworld2.

Defines the Map, which serves tiles, tile labels, and grid outlines. Supports
tile layers.

Map combines view (pygame) and model (world coordinates). It contains a rect
attribute defining its dimensions, and observes pygame coordinate space.

The layers attribute is a two-dimensional list of tile sprites. This can be
accessed directly, or via the class methods. See also the Camera class for
its tile range calculations.

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
        """Construct an instance of Map.
        
        The tile_size argument is a sequence of two ints representing the width
        and height of a tile in pixels.
        
        The map_size argument is a sequence of two ints representing the width
        and height of the map in tiles.
        """
        self.tile_size = Vec2d(tile_size)
        self.map_size = Vec2d(map_size)
        self.layers = []
        
        tw,th = tile_size
        mw,mh = map_size
        self.rect = pygame.Rect(0,0,tw*mw,th*mh)
        
        # grid lines
        def make_line(size):
            s = pygame.sprite.Sprite()
            s.image = pygame.surface.Surface(size)
            s.image.fill(Color('white'))
            s.image.set_alpha(75)
            s.rect = s.image.get_rect()
            return s
        self.h_line = make_line((tw,1))
        self.v_line = make_line((1,th))
        
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
        """Clear all layers.
        """
        del self.layers[:]
    
    def get_tile_at(self, x, y, layer=0):
        """Return the tile at grid location (x,y) in the specified layer. If no
        tile exists at the location, None is returned.
        """
        return self.layers[layer].get((x,y), None)

    def get_tiles(self, x1, y1, x2, y2, layer=0):
        """Return the list of tiles at the specified layer in range (x1,y1)
        through (x2,y2).
        
        The arguments x1,y1,x2,y2 are ints representing the range of tiles to
        select.
        
        The layer argument is an int representing the tile layer to select.
        
        If the layer is not visible, an empty list is returned.
        """
        if self.layers[layer].visible:
            # this is dict.get()
            get = self.layers[layer].get
            return [
                s for s in (
                    get((x,y), None)
                        for x in range(x1,x2)
                            for y in range(y1,y2)
                ) if s
            ]
        else:
            return []

    def get_label_at(self, x, y):
        """Return the label sprite at grid location (x,y). If no sprite exists at
        that location, None is returned.
        """
        return self.labels.get((x,y), None)
    
    def get_labels(self, x1, y1, x2, y2):
        """Return the list of labels in range (x1,y1) through (x2,y2).
        
        The arguments x1,y1,x2,y2 are ints representing the range of labels to
        select.
        """
        # this is dict.get()
        get = self.labels.get
        return [
            s for s in (
                get((x,y), None)
                    for x in range(x1,x2)
                        for y in range(y1,y2)
            ) if s
        ]
    
    def vertical_grid_line(self, xy=None, anchor='topleft'):
        """Return the vertical grid sprite. If specified, the sprite.rect's
        attribute specified by anchor is set to the value of xy.
        """
        v_line = self.v_line
        if xy is not None:
            setattr(v_line.rect, anchor, xy)
        return v_line
    
    def horizontal_grid_line(self, xy=None, anchor='topleft'):
        """Return the horizontal grid sprite. If specified, the sprite.rect's
        attribute specified by anchor is set to the value of xy.
        """
        h_line = self.h_line
        if xy is not None:
            setattr(h_line.rect, anchor, xy)
        return h_line


class MapLayer(dict):
    
    def __init__(self, visible=True):
        """Construct an instance of MapLayer.
        
        Instances of this class can be accessed as dicts to retrieve tiles.
        
        If the visible attribute is True, then this layer is visible. If False,
        it is not visible.
        """
        super(MapLayer, self).__init__()
        self.visible = visible
