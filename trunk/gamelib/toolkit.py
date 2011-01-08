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


__doc__ = """toolkit.py - Some helper tools for Gummworld2.
"""


import pygame
from pygame.locals import RLEACCEL
from pygame.sprite import Sprite

from gamelib import data, State, Map, MapLayer, Vec2d
from gamelib.ui import HUD, Stat, Statf, hud_font
from tiledtmxloader import TileMapParser, ImageLoaderPygame


def make_hud(caption=None):
    """Create a HUD with dynamic items. This creates a default hud to serve
    both as an example, and for an early design and debugging convenience.
    """
    State.hud = HUD()
    next_pos = State.hud.next_pos
    
    if caption:
        State.hud.add('Caption', Stat(next_pos(), caption))
    
    State.hud.add('FPS',
        Statf(next_pos(), 'FPS %d', callback=State.clock.get_fps))
    
    rect = State.world.rect
    l,t,r,b = rect.left,rect.top,rect.right,rect.bottom
    State.hud.add('Bounds',
        Stat(next_pos(), 'Bounds %s'%((int(l),int(t),int(r),int(b)),)) )
    
    def get_mouse():
        s = pygame.mouse.get_pos()
        w = State.camera.screen_to_world(s)
        return 'S'+str(s) + ' W'+str((int(w.x),int(w.y),))
    State.hud.add('Mouse',
        Statf(next_pos(), 'Mouse %s', callback=get_mouse, interval=100))
    
    def get_world_pos():
        s = State.camera.world_to_screen(State.camera.position)
        w = State.camera.position
        return 'S'+str((int(s.x),int(s.y),)) + ' W'+str((int(w.x),int(w.y),))
    State.hud.add('Camera',
        Statf(next_pos(), 'Camera %s', callback=get_world_pos, interval=100))


def make_tiles():
    """Create tiles to fill the current map. This is a utility for easily making
    visible content to aid early game design or debugging.
    
    Tiles transition from top-left to bottom-right, red to blue.
    """
    # Tiles are sprites; each sprite must have a name, an image, and a rect.
    tw,th = State.map.tile_size
    mw,mh = State.map.map_size
    State.map.layers.append(MapLayer(
        State.map.tile_size, State.map.map_size, True, True))
    for x in range(mw):
        for y in range(mh):
            s = pygame.sprite.Sprite()
            s.name = (x,y)
            s.image = pygame.surface.Surface((tw,th))
            facx = max(float(x) / mw, 0.01)
            facy = max(float(y) / mh, 0.01)
            R = 255-255*facx
            G = 0
            B = 255*facy
            s.image.fill((R,G,B))
            s.rect = s.image.get_rect(topleft=(x*tw,y*th))
            State.map.add(s)


def make_tiles2():
    """Create tiles to fill the current map. This is a utility for easily making
    visible content to aid early game design or debugging.
    
    Tiles transition from top to bottom, light blue to brown.
    """
    # Tiles are sprites; each sprite must have a name, an image, and a rect.
    tw,th = State.map.tile_size
    mw,mh = State.map.map_size
    State.map.layers.append(MapLayer(
        State.map.tile_size, State.map.map_size, True, True))
    for x in range(mw):
        for y in range(mh):
            s = pygame.sprite.Sprite()
            s.name = (x,y)
            s.image = pygame.surface.Surface((tw,th))
            facy = max(float(y) / mh, 0.01)
            R = 200-100*facy
            G = 150-100*facy
            B = 249-249*facy
            s.image.fill((R,G,B))
            pygame.draw.line(s.image, (R+9,G+9,B+9), (0,0), (0,th))
            s.rect = s.image.get_rect(topleft=(x*tw,y*th))
            State.map.add(s)


def collapse_map(map, num_tiles=(2,2)):
    """Collapse all layers in a map by combining num_tiles into one tile.
    Returns a new map.
    
    The map argument is the source map. It must be an instance of Map.
    
    The num_tiles argument is a tuple representing the number of tiles in the X
    and Y axes to combine.
    """
    # new map dimensions
    num_tiles = Vec2d(num_tiles)
    tw,th = map.tile_size * num_tiles
    mw,mh = map.map_size // num_tiles
    if mw * num_tiles.x != map.map_size.x:
        mw += 1
    if mh * num_tiles.y != map.map_size.y:
        mh += 1
    # new map
    new_map = Map((tw,th), (mw,mh))
    # collapse the tiles in each layer...
    for layeri,layer in enumerate(map.layers):
        new_layer = collapse_map_layer(map, layeri, num_tiles)
        # add a new layer
        new_map.layers.append(new_layer)
    if hasattr(map, 'tiled_map'):
        new_map.tiled_map = map.tiled_map
    return new_map


def collapse_map_layer(map, layeri, num_tiles=(2,2)):
    """Collapse a single layer in a map by combining num_tiles into one tile.
    
    The map argument is the source map. It must be an instance of Map.
    
    The layeri argument is an int representing the layer index to collapse.
    
    The num_tiles argument is a tuple representing the number of tiles in the X
    and Y axes to combine.
    """
    # new map dimensions
    num_tiles = Vec2d(num_tiles)
    tw,th = map.tile_size * num_tiles
    mw,mh = map.map_size // num_tiles
    if mw * num_tiles.x != map.map_size.x:
        mw += 1
    if mh * num_tiles.y != map.map_size.y:
        mh += 1
    layer = map.layers[layeri]
    new_layer = MapLayer((tw,th), (mw,mh), layer.visible, True, True)
    # walk the old map, stepping by the number of the tiles argument...
    for x in range(0, map.map_size.x, num_tiles.x):
        for y in range(0, map.map_size.y, num_tiles.y):
            # make a new sprite
            s = Sprite()
            s.image = pygame.surface.Surface((tw,th))
            s.rect = s.image.get_rect()
            s.name = tuple((x,y) / num_tiles)
            
            # blit (x,y) tile and neighboring tiles to right and lower...
            tiles = map.get_tiles(x, y, x+num_tiles.x, y+num_tiles.y, layer=layeri)
            if len(tiles):
                # Detect colorkey.
                colorkey = None
                for tile in tiles:
                    c = tile.image.get_colorkey()
                    if c is not None:
                        colorkey = c
                # Fill dest image if there is a colorkey.
                if colorkey is not None:
                    s.image.fill(colorkey)
                # Blit the images (first turning off source colorkey).
                for tile in tiles:
                    nx,ny = Vec2d(tile.name) - (x,y)
                    p = s.rect.topleft + map.tile_size * (nx,ny)
                    copy_image = tile.image.copy()
                    copy_image.set_colorkey(None)
                    s.image.blit(copy_image, p)
                # Set the dest colorkey.
                if colorkey is not None:
                    s.image.set_colorkey(colorkey, RLEACCEL)
##                    s.image.set_alpha(tile.image.get_alpha())
                s.rect.topleft = Vec2d(x,y) * map.tile_size
                new_layer[s.name] = s
    
    return new_layer


def load_tiled_tmx_map(map_file_name):
    """Load an orthogonal TMX map file that was created by the Tiled Map Editor.
    
    Thanks to dr0id for his nice tiledtmxloader module:
        http://www.pygame.org/project-map+loader+for+%27tiled%27-1158-2951.html

    And the creators of Tiled Map Editor:
        http://www.mapeditor.org/
    """
    
    # Taken pretty much verbatim from the tiledtmxloader module.
    #
    # The tiledtmxloader.TileMap object is stored in the returned
    # gamelib.Map object in attribute 'tiled_map'.
    
    world_map = TileMapParser().parse_decode_load(
        data.filepath('map', map_file_name), ImageLoaderPygame())
    tile_size = (world_map.tilewidth, world_map.tileheight)
    map_size = (world_map.width, world_map.height)
    gummworld_map = Map(tile_size, map_size)
    gummworld_map.tiled_map = world_map
    for layeri,layer in enumerate(world_map.layers):
        gummworld_map.layers.append(MapLayer(
            tile_size, map_size, layer.visible, True, True))
        if not layer.visible:
            continue
        for ypos in xrange(0, layer.height):
            for xpos in xrange(0, layer.width):
                x = (xpos + layer.x) * world_map.tilewidth
                y = (ypos + layer.y) * world_map.tileheight
                img_idx = layer.content2D[xpos][ypos]
                offx, offy, screen_img = world_map.indexed_tiles[img_idx]
                sprite = Sprite()
                if screen_img.get_alpha():
                    screen_img = screen_img.convert_alpha()
                else:
                    screen_img = screen_img.convert()
                    if layer.opacity > -1:
                        screen_img.set_alpha(None)
                        alpha_value = int(255. * float(layer.opacity))
                        screen_img.set_alpha(alpha_value)
                sprite.image = screen_img.convert_alpha()
                sprite.rect = screen_img.get_rect(topleft=(x,y))
                sprite.name = xpos,ypos
                gummworld_map.add(sprite, layer=layeri)
    return gummworld_map


def draw_sprite(s, blit_flags=0):
    """Draw a sprite on the camera's surface using world-to-screen conversion.
    """
    camera = State.camera
    cx,cy = camera.rect.topleft
    sx,sy = s.rect.topleft
    camera.surface.blit(s.image, (sx-cx, sy-cy), special_flags=blit_flags)


def interpolated_step(pos, step, interp):
    """Returns (float,float).
    
    This is a utility for drawing routines, after pos has been updated by step.
    For example:
        def update():
            move_camera()
            State.camera.update()
            sprite_group.update()  # e.g. steps a sprite position
        def draw():
            interp = State.camera.interpolate()
            camera_pos = State.camera.rect.topleft
            for s in sprite_group:
                sprite_pos = Vec2d(s.rect.topleft)
                pos = sprite_pos - camera_pos
                step = s.step
                interp_pos = toolkit.interpolated_step(pos, step, interp)
                surf.blit(s.image, interp_pos)
    """
    # Interpolated step = step * interpolation factor
    interp_step = Vec2d(step) * interp
    
    # Interpolated pos = screen_pos - step + interpolated step
    x,y = pos
    pos = float(x),float(y)
    return pos - step + interp_step


def draw_tiles():
    """Draw visible tiles.
    
    This function assumes that the tiles stored in the map are sprites.
    """
    for layer in State.camera.visible_tiles:
        # the list comprehension filters out sprites that are None
        for s in layer.values():
            draw_sprite(s)


def draw_labels(layer=0):
    """Draw visible labels if enabled.
    
    Labels for the specified layer are blitted to the camera surface. If the
    layer has been collapsed with the collapse_map_layer() function so that
    the layer's tile size differs from the grid label sprites, this will look
    weird.
    """
    if State.show_labels:
        x1,y1,x2,y2 = State.camera.visible_tile_range[layer]
        map_layer = State.map.layers[layer]
        get = map_layer.get_labels
        for s in get(x1,y1,x2,y2):
            draw_sprite(s)


def draw_grid(layer=0):
    """Draw grid if enabled.
    
    Grids for the specified layer are blitted to the camera surface. If the layer
    has been collapsed with the collapse_map_layer() function so that the
    layer's tile size differs from the grid line sprites, this will look weird.
    """
    if State.show_grid:
        x1,y1,x2,y2 = State.camera.visible_tile_range[layer]
        # speed up access to grid lines and their rects
        map = State.map
        map_layer = map.layers[layer]
        hline = map_layer.h_line
        vline = map_layer.v_line
        hrect = hline.rect
        vrect = vline.rect
        for s in map.get_tiles(x1, y1, x2, y2):
            srect = s.rect
            hrect.topleft = srect.bottomleft
            draw_sprite(hline)
            vrect.topleft = srect.topright
            draw_sprite(vline)
