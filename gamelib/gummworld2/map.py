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


__doc__ = """map.py - Map module for Gummworld2.

Defines the Map, which serves tiles, tile labels, and grid outlines. Supports
tile layers.

Map combines view (pygame) and model (world coordinates). It contains a rect
attribute defining its dimensions, and observes pygame coordinate space.

The layers attribute is a two-dimensional list of tile sprites. This can be
accessed directly, or via the class methods. See also the Camera class for
its visible tile range utilities.

IMPORTANT: Map instance variables tile_size and map_size define the *original*
dimensions of the map. Map layers can support individual tile sizes and map
sizes. When rendering a layer one should use the MapLayer instance variables
instead. This is especially important for two cases:
    
    1. Loading a map that uses layers with different tile sizes.
    2. Using toolkit.collapse_map_layer() to resize a layer.

If a map has only one layer, or all layers have the same dimensions it is safe
to use the Map instance variables tile_size and map_size.

It may help to see a code representation. Here are two layers, one with 32x32
tiles and another with 64x64 tiles. Note that both layer sizes in pixels are the
same (320x320 pixels) but the map grids are at 10 and 5 respectively.
    
    map.layers = [
        MapLayer((32,32), (10,10)),
        MapLayer((64,64), (5,5)),
    ]

The sprites for grid lines and grid labels are created when each map layer is
created. The toolkit.collapse_* functions also convert these sprites.

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

from gummworld2 import data, Vec2d
from gummworld2.ui import text_color


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
        self.subpixel_cache = {}
        
        tw,th = tile_size
        mw,mh = map_size
        self.rect = pygame.Rect(0,0,tw*mw,th*mh)
    
    def add(self, *tiles, **kwargs):
        """Map.add(*tiles, layer=0)
        """
        layeri = kwargs.get('layer', 0)
        layer = self.layers[layeri]
        for s in tiles:
#            if not isinstance(s, pygame.sprite.Sprite):
#                raise pygame.error, '*tiles argument must be one or more sprites'
#            if not isinstance(s.name, tuple):
#                raise pygame.error, 'name property must be an (x,y) tuple'
            layer.append(s)
    
    def clear(self):
        """Clear all layers.
        """
        del self.layers[:]
    
    def get_tile_at(self, x, y, layer=0):
        """Return the tile at grid location (x,y) in the specified layer. If no
        tile exists at the location, None is returned.
        """
        return self.layers[layer].get_tile_at(x, y)

    def get_tiles(self, x1, y1, x2, y2, layer=0):
        """Return the list of tiles at the specified layer in range (x1,y1)
        through (x2,y2).
        
        The arguments x1,y1,x2,y2 are ints representing the range of tiles to
        select.
        
        The layer argument is an int representing the tile layer to select.
        
        If the layer is not visible, an empty list is returned.
        """
        return self.layers[layer].get_tiles(x1,y1,x2,y2)
    
    def get_tiles_in_rect(self, rect, layer=0):
        return self.layers[layeri].get_tiles_in_rect(rect)
    

class MapLayer(list):
    
    def __init__(self, tile_size, map_size, visible=True,
        make_labels=False, make_grid=False, name=''):
        """Construct an instance of MapLayer.
        
        Instances of this class can be accessed as dicts to retrieve tiles.
        
        If the visible attribute is True, then this layer is visible. If False,
        it is not visible.
        
        The name attribute is reserved for programmer convenience. It is not
        used by the Gummworld2 library.
        
        NOTE: For do-it-yerself tile access. MapLayer is a breadth-first flat
        list, i.e.: it is not a nested list of lists; each row's tiles is
        stored contiguously; position (x=0,y=0) is element 0, (x=1,y=0) is
        element 1, and so on. It should be loaded and read by loops like so:
            
            for y in range(top, bottom):
                for x in range(left, right):
                    pass
        
        Array math can be used to access rows and partial rows as slices:
            
            map_width = layer.map_size[0]
            row = 2
            left = 10
            right = 20
            row_idx = row*map_width
            tiles = layer[row_idx+left : row_idx+right]
        
        It is very likely desirable not to return tiles when x<0 or
        x>=map_width, and when y<0 or y>map_height. See the source of
        get_tile_at() for an example.
        """
        super(MapLayer, self).__init__()
        self.tile_size = tile_size
        self.map_size = map_size
        self.visible = visible
        self.name = name

        tw,th = tile_size
        mw,mh = map_size
        
        # grid lines
        if make_grid:
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
        if make_labels:
            font = pygame.font.Font(data.filepath('font', 'Vera.ttf'), 8)
            for x in range(0,mw):
                for y in range(0,mh):
                    s = pygame.sprite.Sprite()
                    s.image = font.render('%d,%d'%(x,y), True, text_color)
                    s.rect = s.image.get_rect(
                        topleft=Vec2d(x*tw,y*th)+(2,2))
                    self.labels[x,y] = s
    
    def get_tile_at(self, x, y):
        """Return the tile at grid location (x,y). If no tile exists at the
        location, None is returned.
        """
        mapw,maph = self.map_size
        if x < 0 or y < 0:
            return None
        if x >= mapw or y >= maph:
            return None
        try:
            return self[y*mapw+x]
        except IndexError:
            return None
    
    def set_tile_at(self, x, y, tile):
        """Set the value of grid location (x,y) to tile.
        
        This method performs no sanity check or adjustments on x or y. If x or y
        are calculated without regard to this layer's map size, an IndexError
        exception may occur, or may give unexpected results if x is negative or
        larger than map width.
        """
        mapw = self.map_size[0]
        self[y*mapw+x] = tile
    
    def get_tiles(self, x1, y1, x2, y2):
        """Return the list of tiles in range (x1,y1) through (x2,y2).
        
        The arguments x1,y1,x2,y2 are ints representing the range of tiles to
        select.
        
        If the layer is not visible, an empty list is returned.
        """
        tiles = []
        if self.visible:
            mw,mh = self.map_size
            if x1 < 0: x1 = 0
            if y1 < 0: y1 = 0
            if x2 > mw: x2 = mw
            if y2 > mh: y2 = mh
            for y in range(y1,y2):
                start = y*mw+x1
                end = y*mw+x2
                tiles.extend(self[start:end])
        return tiles
    
    def get_tiles_in_rect(self, rect):
        tile_x,tile_y = self.tile_size
        l,t,w,h = rect
        r = l+w-1
        b = t+h-1
        left = int(round(float(l) / tile_x))
        right = int(round(float(r) / tile_x))
        top = int(round(float(t) / tile_y))
        bottom = int(round(float(b) / tile_y))
        tiles = self.get_tiles(left, top, right, bottom)
        return tiles
    
    def index_of(self, x, y):
        """Return the array index relating to grid location (x,y).
        
        This method performs no sanity check or adjustments on x or y. If x or y
        are calculated without regard to this layer's map size, the return value
        may be an invalid index, or may be an unexpected value if x is negative
        or larger than map width..
        """
        mapw = self.map_size[0]
        return y * mapw + x
    
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
