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


__doc__ = """tiledmap.py - Tiled Map module for Gummworld2.

See basicmap module for the basic docs.

These classes add support for Tiled maps loaded by tiletmxloader.
"""

import pygame

from tiledtmxloader.helperspygame import get_layers_from_map, SpriteLayer
from tiledtmxloader.tmxreader import TileMap, TileMapParser
from tiledtmxloader.helperspygame import ResourceLoaderPygame, RendererPygame

from gummworld2 import spatialhash
from gummworld2.basicmap import BasicMap, BasicLayer, collapse_layer, blit_layer


class TiledMap(BasicMap):
    
    def __init__(self, map_file_name, collapse=(1,1), collapse_layers=None, load_invisible=True):
        """Construct a TiledMap object.
        
        the map_file_name argument is the path and filename of the TMX map file.
        
        The collapse argument is the number of tiles on the X and Y axes to
        join.
        
        The collapse_layers argument is a sequence of indices indicating to
        which TiledMap.layers the collapse algorithm should be applied. See the
        tiledmap.collapse_map.
        
        If you don't want every layer collapsed, or different collapse values
        per layer, use the default of (1,1) and pick individual tile layers to
        collapse via TileMap.collapse(), collapse_map(), or collapse_layer().
        """
        self.layers = []
        
        self.raw_map = TileMapParser().parse_decode(map_file_name)
        
        self.width = self.raw_map.width
        self.height = self.raw_map.height
        self.tile_width = self.raw_map.tilewidth
        self.tile_height = self.raw_map.tileheight
        self.pixel_width = self.raw_map.pixel_width
        self.pixel_height = self.raw_map.pixel_height
        
        self.rect = pygame.Rect(0,0,self.pixel_width,self.pixel_height)
        
        self.orientation = self.raw_map.orientation
        self.properties = self.raw_map.properties
        self.map_file_name = self.raw_map.map_file_name
        self.named_layers = self.raw_map.named_layers
        
        _load_tiled_tmx_map(self.raw_map, self, load_invisible)
        
        if collapse > (1,1):
            self.collapse(collapse, collapse_layers)
    
    def get_layer_by_name(self, layer_name):
        return self.named_layers[layer_name]
    
    def get_tile_layers(self):
        rl = self.layers
        return [L for L in self.layers if not L.is_object_group]
    
    def get_object_groups(self):
        return [L for L in self.layers if L.is_object_group]


class TiledLayer(object):
    
    def __init__(self, parent_map, layer, layeri):
        import sys
        
        self.parent_map = parent_map
        self.is_object_group = layer.is_object_group
        self.name = layer.name
        
        self.width = parent_map.width
        self.height = parent_map.height
        self.tile_width = parent_map.tile_width
        self.tile_height = parent_map.tile_height
        self.pixel_width = parent_map.pixel_width
        self.pixel_height = parent_map.pixel_height
        
        if self.is_object_group:
            self.opacity = 1
        else:
            self.opacity = layer.opacity
        cell_size = max(self.tile_width, self.tile_height)
        self.rect = pygame.Rect(0,0, self.pixel_width+1, self.pixel_height+1)
        self.objects = spatialhash.SpatialHash(self.rect, cell_size)
        
        self.layeri = layeri
        
        self.name = layer.name
        self.properties = layer.properties
        self.visible = layer.visible
    
    def add(self, tile):
        self.objects.add(tile)
    
    def get_objects_in_rect(self, rect):
        return self.objects.intersect_rect(rect)
    
    def __len__(self):
        return len(self.objects.cell_ids)
    
    def collapse(self, collapse=(1,1)):
        if self.is_object_group or collapse <= (1,1):
            return
        new_layer = TiledLayer(self.parent_map, self, self.layeri)
        collapse_layer(self, new_layer, collapse)
        self.parent_map.layers[self.layeri] = new_layer
    
    def blit_layer(self, src_layer):
        if self.is_object_group:
            return
        blit_layer(self, src_layer)
    
    def __iter__(self):
        return iter(self.objects)


def _load_tiled_tmx_map(tmx_map, gummworld_map, load_invisible=True):
    """Load an orthogonal TMX map file that was created by the Tiled Map Editor.
    
    If load_invisible is False, layers where visible!=0 will be empty. Their
    tiles will not be loaded.
    
    Thanks to DR0ID for his nice tiledtmxloader module:
        http://www.pygame.org/project-map+loader+for+%27tiled%27-1158-2951.html
    
    And the creators of Tiled Map Editor:
        http://www.mapeditor.org/
    """
    
    # Taken pretty much verbatim from the (old) tiledtmxloader module.
    
    from pygame.sprite import Sprite
    
    resource = ResourceLoaderPygame()
    resource.load(tmx_map)
    tile_size = (tmx_map.tilewidth, tmx_map.tileheight)
    map_size = (tmx_map.width, tmx_map.height)
    
    for layeri,layer in enumerate(tmx_map.layers):
        gummworld_layer = TiledLayer(gummworld_map, layer, layeri)
        gummworld_map.layers.append(gummworld_layer)
        if not layer.visible and not load_invisible:
            continue
        if layer.is_object_group:
            for obj in layer.objects:
                sprite = Sprite()
                sprite.image = obj.image
                sprite.rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                sprite.type = obj.type
                sprite.image_source = obj.image_source
                sprite.name = obj.name
                sprite.properties = obj.properties
                gummworld_layer.add(sprite)
        else:
            for ypos in xrange(0, layer.height):
                for xpos in xrange(0, layer.width):
                    x = (xpos + layer.x) * layer.tilewidth
                    y = (ypos + layer.y) * layer.tileheight
                    img_idx = layer.content2D[xpos][ypos]
                    if img_idx == 0:
                        continue
                    try:
                        offx,offy,tile_img = resource.indexed_tiles[img_idx]
                        screen_img = tile_img
                    except KeyError:
                        print 'KeyError',img_idx,(xpos,ypos)
                        continue
                    sprite = Sprite()
                    ## Note: alpha conversion can actually kill performance.
                    ## Do it only if there's a benefit.
#                    if convert_alpha:
#                        if screen_img.get_alpha():
#                            screen_img = screen_img.convert_alpha()
#                        else:
#                            screen_img = screen_img.convert()
#                            if layer.opacity > -1:
#                                screen_img.set_alpha(None)
#                                alpha_value = int(255. * float(layer.opacity))
#                                screen_img.set_alpha(alpha_value)
#                                screen_img = screen_img.convert_alpha()
                    sprite.image = screen_img
                    sprite.rect = screen_img.get_rect(topleft=(x + offx, y + offy))
                    sprite.name = xpos,ypos
                    gummworld_layer.add(sprite)
