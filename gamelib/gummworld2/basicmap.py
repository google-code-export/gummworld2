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


__doc__ = """basicmap.py - Basic Map module for Gummworld2.

Defines the BasicMap, which serves layers and sprite objects.

BasicMap combines view (pygame) and model (world coordinates). It contains a
rect attribute defining its dimensions, and observes pygame coordinate space.

The layers attribute is a spatialhash containing sprites. This can be
accessed directly, or via the class methods. See also the toolkit module for
convenience utilities.

The caller must manage maps and their corresponding worlds by swapping the
State.map and State.world package globals, for example:
    
    # Create the initial map and world, and save it.
    State.map = BasicMap(width, height, tile_width, tile_height)
    State.world = model.World(State.map.rect)
    levels = []
    levels.append((State.map,State.world))
    ...
    # Create a new one, save it.
    State.map = BasicMap(new_width, new_height, new_tile_width, new_tile_height)
    State.world = model.World(State.map.rect)
    levels.append((State.map,State.world))
    ...
    # Restore a map and world.
    State.map,State.world = levels[0]
    
Alternatively State.save() and State.restore() can be used to facilitate this.
"""


import pygame

from gummworld2 import data, spatialhash, Vec2d
from gummworld2.ui import text_color


class BasicMap(object):
    
    def __init__(self, width, height, tile_width, tile_height):
        """Construct a BasicMap object.
        """
        self.layers = []
        
        self.pixel_width = width * tile_width
        self.pixel_height = height * tile_height
        self.width = width
        self.height = height
        self.tile_width = tile_width
        self.tile_height = tile_height
        
        self.rect = pygame.Rect(0,0,self.pixel_width,self.pixel_height)
    
    def get_layer(self, layer_index):
        return self.layers[layer_index]
    
    def get_layers(self, which_layers=None):
        if not which_layers:
            which_layers = range(len(self.layers))
        return [L for i,L in enumerate(self.layers) if i in which_layers]
    
    def get_objects_in_rect(self, rect, layeri=0):
        tiles = []
        content2D = self.get_layer(layeri).content2D
        x1,y1,x2,y2 = self.rect_to_range(rect, layeri)
        for column in content2D[x1:x2+1]:
            tiles.extend([t for t in column[y1:y2+1] if t])
        return tiles
    
    def collapse(self, collapse=(1,1), which_layers=None):
        """Collapse which_layers by joining num_tiles into one tile. The
        original layers are replaced by new layers.
        
        The collapse argument is the number of tiles on the X and Y axes to
        join.
        
        The collapse_layers argument is a sequence of indices indicating to
        which TiledMap.layers the collapse algorithm should be applied. See the
        tiledmap.collapse_map.
        """
        if collapse <= (1,1):
            return
        if which_layers is None:
            which_layers = range(len(self.layers))
        for layeri in which_layers:
            self.layers[layeri].collapse(collapse)
    
    def merge_layers(self, which_layers=None):
        if which_layers is None:
            which_layers = range(len(self.layers))
        if len(which_layers) < 2:
            return
        dest_layer = self.layers[which_layers[0]]
        del_layers = []
        for layeri in which_layers[1:]:
##            print 'blit_layer'
            src_layer = self.layers[layeri]
            dest_layer.blit_layer(src_layer)
            del_layers.append(src_layer)
        for layer in del_layers:
##            print 'del layer'
            self.layers.remove(layer)


class BasicLayer(object):
    
    def __init__(self, parent_map, layer_index, cell_size=None):
        self.parent_map = parent_map
        
        self.tile_width = parent_map.tile_width
        self.tile_height = parent_map.tile_height
        self.width = parent_map.width
        self.height = parent_map.height
        self.pixel_width = self.width * self.tile_width
        self.pixel_height = self.height * self.tile_height
        
        if cell_size == None:
            cell_size = max(self.tile_width, self.tile_height)
        self.rect = pygame.Rect(0,0, self.pixel_width+1, self.pixel_height+1)
        self.objects = spatialhash.SpatialHash(self.rect, cell_size)
        
        self.layeri = layer_index
        self.visible = True
    
    def add(self, tile):
        self.objects.add(tile)
    
    def get_objects_in_rect(self, rect):
        return self.objects.intersect_objects(rect)
    
    def collapse(self, collapse=(1,1)):
        if collapse <= (1,1):
            return
        new_layer = BasicLayer(self.parent_map, self.layeri)
        collapse_layer(self, new_layer, collapse)
        self.parent_map.layers[self.layeri] = new_layer
    
    def blit_layer(self, src_layer):
        blit_layer(self, src_layer)
    
    def __iter__(self):
        return iter(self.objects)


def collapse_layer(old_layer, new_layer, num_tiles=(2,2)):
    """Collapse a single layer by joining num_tiles into one tile. A new layer
    is returned.
    
    The old_layer argument is the layer to process.
    
    The new_layer argument is the layer to build.
    
    The num_tiles argument is a tuple representing the number of tiles in the X
    and Y axes to join.
    
    If a map area is sparse (fewer tiles than num_tiles[0] * num_tiles[1]) the
    tiles will be kept as they are.
    
    If tiles with different characteristics are joined, the results can be
    unexpected. These characteristics include some flags, depth, colorkey. This
    can be avoided by pre-processing the map to convert all images so they have
    compatible characteristics.
    """
    from pygame.sprite import Sprite
    from gummworld2 import Vec2d
    
    # New layer dimensions.
    num_tiles = Vec2d(num_tiles)
    tw,th = (old_layer.tile_width,old_layer.tile_height) * num_tiles
    mw,mh = (old_layer.width,old_layer.height) // num_tiles
    if mw * num_tiles.x != old_layer.pixel_width:
        mw += 1
    if mh * num_tiles.y != old_layer.pixel_height:
        mh += 1
    # Poke the right values into new_layer.
    cell_size = max(tw,th) * 2
    new_layer.objects = spatialhash.SpatialHash(old_layer.rect, cell_size)
    new_layer.width = mw
    new_layer.height = mh
    new_layer.tile_width = tw
    new_layer.tile_height = th
    # Grab groups of map sprites, joining them into a single larger image.
    query_rect = pygame.Rect(0,0,tw-1,th-1)
    for y in range(0, mh*th, th):
        for x in range(0, mw*tw, tw):
            query_rect.topleft = x,y
            sprites = old_layer.objects.intersect_objects(query_rect)
            if len(sprites) != num_tiles.x * num_tiles.y:
                for s in sprites:
                    new_layer.add(s)
                continue
            # If sprite images have different characteristics, they cannot be
            # reliably collapsed. In which case, keep them as-is.
            incompatible = False
            image = sprites[0].image
            flags = image.get_flags() ^ pygame.SRCALPHA
            colorkey = image.get_colorkey()
            depth = image.get_bitsize()
# This is probably too restrictive. However, some combinations of tiles may
# give funky results.
#            all_details = (flags,colorkey,depth)
#            for s in sprites[1:]:
#                if all_details != (
#                        s.image.get_flags(),
#                        s.image.get_colorkey(),
#                        s.image.get_bitsize(),
#                ):
#                    incompatible = True
#            if incompatible:
#                print 'collapse_layer: incompatible image characteristics'
#                for s in sprites:
#                    new_layer.add(s)
#                continue
            # Make a new sprite.
            new_sprite = Sprite()
            new_sprite.rect = sprites[0].rect.unionall([s.rect for s in sprites[1:]])
            new_sprite.rect.topleft = x,y
            new_sprite.image = pygame.surface.Surface(new_sprite.rect.size, flags, depth)
            if colorkey:
                new_sprite.image.set_colorkey(colorkey)
            
            # Blit (x,y) tile and neighboring tiles to right and lower...
            left = reduce(min, [s.rect.x for s in sprites])
            top = reduce(min, [s.rect.y for s in sprites])
            for sprite in sprites:
                p = sprite.rect.x - left, sprite.rect.y - top
                new_sprite.image.blit(sprite.image.convert(depth, flags), p)
            new_layer.add(new_sprite)
    return new_layer


def blit_layer(dest_layer, src_layer):
    for dest_sprite in dest_layer:
        dimage = dest_sprite.image.copy()
        drect = dest_sprite.rect
        for src_sprite in src_layer:
            simage = src_sprite.image
            srect = src_sprite.rect
            x = srect.x - drect.x
            y = srect.y - drect.y
            dimage.blit(src_sprite.image, (x,y))
        dest_sprite.image = dimage
