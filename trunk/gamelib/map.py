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


__version__ = '0.1'
__vernum__ = (0,1)


"""map.py - Map module for Gummworld2.

Defines the Map, which serves tiles, tile labels, and grid outlines.

Map also sets these package globals:
    
    State.tile_size
    State.map_size

Map is purely view (pygame). It contains a rect attribute defining its
dimensions, and observes pygame coordinate space.

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
"""
import pygame
from pygame.locals import Color

import model
from state import State
from ui import hud_font, text_color
from vec2d import Vec2d

class Map(object):
    
    def __init__(self, tile_size, map_size):
        State.tile_size = Vec2d(tile_size)
        State.map_size = Vec2d(map_size)
        self.tiles = {}

        tw,th = tile_size
        mw,mh = map_size
        self.rect = pygame.Rect(0,0,tw*mw,th*mh)
        
#        rect = self.rect
#        State.world = model.World(self.rect)

        # make a tile outline to blit for optional grid
        s = pygame.sprite.Sprite()
        s.image = pygame.surface.Surface((tw,th))
        s.rect = s.image.get_rect()
        pygame.draw.rect(s.image, Color('white'), s.rect, 1)
        s.image.set_colorkey(Color('black'))
        s.image.set_alpha(99)
        self.outline = s

        # make grid labels to blit
        self.labels = {}
        for x in range(0,State.map_size.x):
            for y in range(0,State.map_size.y):
                s = pygame.sprite.Sprite()
                s.image = hud_font.render('%d,%d'%(x,y), True, text_color)
                s.image.set_alpha(99)
                s.rect = s.image.get_rect(
                    topleft=Vec2d(x*tw,y*th)+(2,2))
                self.labels[x,y] = s

    def add(self, *tiles):
        for s in tiles:
            if not isinstance(s, pygame.sprite.Sprite):
                raise pygame.error, '*tiles argument must be one or more sprites'
            if not isinstance(s.name, tuple):
                raise pygame.error, 'name property must be an (x,y) tuple'
            self.tiles[s.name] = s

    def clear(self):
        self.tiles.clear()

    def remove(self, x, y):
        tile = self.get_tile_at(x, y)
        del self.tiles[x,y]
        return tile

    def get_tile_at(self, x, y):
        return self.tiles.get((x,y), (None,(x,y)))

    def get_tiles(self, x1, y1, x2, y2):
        return [self.tiles.get((x,y), (None,(x,y)))
            for x in range(x1,x2)
                for y in range(y1,y2)]

    def get_label_at(self, x, y):
        return self.labels.get((x,y), (None,(x,y)))

    def get_labels(self, x1, y1, x2, y2):
        return [self.labels.get((x,y), (None,(x,y)))
            for x in range(x1,x2)
                for y in range(y1,y2)]

    def vertical_grid_line(self, xy=None, anchor='topleft'):
        if xy is not None:
            setattr(self.v_line, anchor, xy)
        return self.v_line

    def horizontal_grid_line(self, xy=None, anchor='topleft'):
        if xy is not None:
            setattr(self.h_line, anchor, xy)
        return self.h_line


if __name__ == '__main__':
    import view
    from camera import Camera
    from map import Map
    from events import EditorEvents
    
    State.screen = view.Screen((400,400))
    State.camera = Camera((0,0))
    State.events = EditorEvents()

    State.grid = True
    State.hud = True
    State.map = Map((128,128),(4,4))

    dt = int(1.0 / 60.0 * 1000)

    while 1:
        pygame.time.wait(dt)
        State.screen.clear()
        State.map.draw_grid()
        State.screen.flip()
        State.events.get()
        State.camera.update(State.world.avatar.position)
