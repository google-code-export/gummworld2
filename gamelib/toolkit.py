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

from state import State
import ui
from ui import HUD, Stat, Statf


def make_tiles():
    """Create tiles to fill the current map. This is a utility for easily making
    visible content to aid early game design or debugging.
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
            s.image.fill((255-255*facx,0,255*facy))
            s.rect = s.image.get_rect(topleft=(x*tw,y*th))
            State.map.add(s)


def make_hud():
    """Create a HUD with dynamic items. This creates a default hud to serve
    both as an example, and for an early design and debugging convenience.
    """
    screen_rect = State.screen.rect
    top = 5
    height = ui.hud_font.get_height()
    y = lambda n: top+height*n
    x = screen_rect.x + 5
    State.hud = HUD()
    
    i = 0
    State.hud.add('FPS',
        Statf((x,y(i)), 'FPS %d', callback=State.clock.get_fps))
    
    i += 1
    def get_world_pos(): p = State.camera.position; return int(p.x),int(p.y)
    State.hud.add('WORLD_POS',
        Statf((x,y(i)), 'World %s', callback=get_world_pos, interval=100))
    
    i += 1
    def get_camera_pos():
        x,y = State.camera.rect.center
        return int(x),int(y)
    State.hud.add('CAMERA_POS',
        Statf((x,y(i)), 'Camera %s', callback=get_camera_pos, interval=100))
    
    i += 1
    bb = State.world.bounding_box
    l,b,r,t = bb.left,bb.bottom,bb.right,bb.top
    State.hud.add('WORLD_BOUNDS',
        Stat((x,y(i)), 'Bounds %s'%((int(l),int(b),int(r),int(t),),)))


def draw_sprite(s):
    """Draw a sprite on the camera's surface using world-to-screen conversion.
    """
    camera = State.camera
    if isinstance(s, Sprite):
        cr = camera.rect
        sr = s.rect
        camera.surface.blit(s.image, (sr.x-cr.x, sr.y-cr.y))


def draw_tiles():
    """Draw visible tiles.
    """
    for s in State.camera.visible_tiles:
        draw_sprite(s)


def draw_labels():
    """Draw visible labels if enabled.
    """
    if State.show_labels:
        x1,y1,x2,y2 = State.camera.visible_tile_range
        get_at = State.map.get_label_at
        for x in range(x1,x2):
            for y in range(y1,y2):
                s = get_at(x,y)
                draw_sprite(s)


def draw_grid():
    """Draw grid if enabled.
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
