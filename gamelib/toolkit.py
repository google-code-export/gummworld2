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


"""toolkit.py - Some helper tools for Gummworld2.
"""


import pygame
from pygame.sprite import Sprite

from gamelib import data, State, Map
from gamelib.ui import HUD, Stat, Statf, hud_font
from tiledtmxloader import TileMapParser, ImageLoaderPygame


def make_tiles():
    """make_tiles() : None
    
    Create tiles to fill the current map. This is a utility for easily making
    visible content to aid early game design or debugging.
    
    Tiles transition from top-left to bottom-right, red to blue.
    """
    # Tiles are sprites; each sprite must have a name, an image, and a rect.
    tw,th = State.tile_size
    mw,mh = State.map_size
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
    """make_tiles2() : None
    
    Create tiles to fill the current map. This is a utility for easily making
    visible content to aid early game design or debugging.
    
    Tiles transition from top to bottom, light blue to brown.
    """
    # Tiles are sprites; each sprite must have a name, an image, and a rect.
    tw,th = State.tile_size
    mw,mh = State.map_size
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


def make_hud():
    """make_hud() : None
    
    Create a HUD with dynamic items. This creates a default hud to serve
    both as an example, and for an early design and debugging convenience.
    """
    State.hud = HUD()
    next_pos = State.hud.next_pos
    
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


def load_tiled_map(map_file_name):
    """load_tiled_map(map_file_name) : gamelib.Map
    
    Load an orthogonal TMX map file that was created by the Tiled Map Editor.
    
    Thanks to dr0id for his nice tiledtmxloader module:
        http://www.pygame.org/project-map+loader+for+%27tiled%27-1158-2951.html

    And the creators of Tiled Map Editor:
        http://www.mapeditor.org/
    """
    
    # Taken pretty much verbatim from the tiledtmxloader module.
    #
    # gamelib.Map does not support layers (yet). We loop through them here
    # but there is no benefit, and will give undesirable results if the map
    # does have multiple layers.
    
    world_map = TileMapParser().parse_decode_load(
        data.filepath('map', map_file_name), ImageLoaderPygame())
    tile_size = (world_map.tilewidth, world_map.tileheight)
    map_size = (world_map.width, world_map.height)
    gummworld_map = Map(tile_size, map_size)
    for layer in world_map.layers:
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
                gummworld_map.add(sprite)
    return gummworld_map


def draw_sprite(s, blit_flags=0):
    """draw_sprite(s, blit_flags=0) : None
    
    Draw a sprite on the camera's surface using world-to-screen conversion.
    """
    camera = State.camera
    if isinstance(s, Sprite):
        cr = camera.rect
        sr = s.rect
        camera.surface.blit(s.image, (sr.x-cr.x, sr.y-cr.y), special_flags=blit_flags)


def draw_tiles():
    """draw_tiles() : None
    
    Draw visible tiles.
    """
    for s in State.camera.visible_tiles:
        draw_sprite(s)


def draw_labels():
    """draw_labels() : None
    
    Draw visible labels if enabled.
    """
    if State.show_labels:
        x1,y1,x2,y2 = State.camera.visible_tile_range
        get_at = State.map.get_label_at
        for x in range(x1,x2):
            for y in range(y1,y2):
                s = get_at(x,y)
                draw_sprite(s)


def draw_grid():
    """draw_grid() : None
    
    Draw grid if enabled.
    """
    if State.show_grid:
        x1,y1,x2,y2 = State.camera.visible_tile_range
        SpriteClass = pygame.sprite.Sprite
        grid = State.map.outline
        rect = grid.rect
        for s in State.map.get_tiles(x1, y1, x2, y2):
            if isinstance(s, SpriteClass):
                rect.topleft = s.rect.topleft
                draw_sprite(grid)
