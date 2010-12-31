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


__doc__ = """toolkit.py - Some helper tools for Gummworld2.
"""


import pygame
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
    State.map.layers.append(MapLayer())
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
    State.map.layers.append(MapLayer())
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


def collapse_map(map, tiles=(2,2)):
    # new map dimensions
    tiles = Vec2d(tiles)
    tw,th = map.tile_size * tiles
    mw,mh = map.map_size // tiles
    if mw * tiles.x != map.map_size.x:
        mw += 1
    if mh * tiles.y != map.map_size.y:
        mh += 1
    # new map
    new_map = Map((tw,th), (mw,mh))
    # collapse the tiles in each layer...
    for layeri,layer in enumerate(map.layers):
        # add a new layer
        new_map.layers.append(MapLayer(layer.visible))
        # walk the old map, stepping by the number of the tiles argument...
        for x in range(0, map.map_size.x, tiles.x):
            for y in range(0, map.map_size.y, tiles.y):
                # make a new sprite
                s = Sprite()
                s.image = pygame.surface.Surface((tw,th))
                s.rect = s.image.get_rect()
                s.name = tuple((x,y) / tiles)
                # blit the (x,y) tile and neighboring tiles to right and lower
##                print '-'*5
##                print 'new tile',(x,y)
                for nx in range(tiles.x):
                    for ny in range(tiles.y):
                        tile = map.get_tile_at(x+nx, y+ny, layeri)
                        if tile:
                            p = s.rect.topleft + map.tile_size * (nx,ny)
##                            print 'blit',p
                            s.image.blit(tile.image, p)
##                            s.image.set_alpha(tile.image.get_alpha())
                s.rect.topleft = Vec2d(x,y) * map.tile_size
##                print 'position',s.rect.topleft
                #
                new_map.add(s, layer=layeri)
    if hasattr(map, 'tiled_map'):
        new_map.tiled_map = map.tiled_map
    return new_map


def load_tiled_map(map_file_name):
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
        gummworld_map.layers.append(MapLayer(layer.visible))
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


def draw_tiles():
    """Draw visible tiles.
    
    This function assumes that the tiles stored in the map are sprites.
    """
    for layer in State.camera.visible_tiles:
        # the list comprehension filters out sprites that are None
        for s in layer:
            draw_sprite(s)


def draw_labels():
    """Draw visible labels if enabled.
    """
    if State.show_labels:
        x1,y1,x2,y2 = State.camera.visible_tile_range
        for s in State.map.get_labels(x1,y1,x2,y2):
            draw_sprite(s)


def draw_grid():
    """Draw grid if enabled.
    """
    if State.show_grid:
        x1,y1,x2,y2 = State.camera.visible_tile_range
        # speed up access to grid lines and their rects
        map = State.map
        hline = map.h_line
        vline = map.v_line
        hrect = hline.rect
        vrect = vline.rect
        for s in map.get_tiles(x1, y1, x2, y2):
            srect = s.rect
            hrect.topleft = srect.bottomleft
            draw_sprite(hline)
            vrect.topleft = srect.topright
            draw_sprite(vline)
