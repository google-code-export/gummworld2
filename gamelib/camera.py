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


"""camera.py - Camera module for Gummworld2.
"""


import pygame

from state import State
from vec2d import Vec2d


class Camera(object):
  
    def __init__(self, target, surface, rect):
        self.target = target
        self.surface = surface
        self.rect = rect

    def update(self):
        if self.rect.center != self.target.position:
            self.rect.center = self.target.position

    @property
    def position(self):
        return self.target.position
   
    @property
    def screen_position(self):
        return Vec2d(self.world_position) - self.rect.topleft

    def world_to_screen(self, xy):
        cx,cy = self.rect.center
        sx,sy = State.screen.rect.center
        x,y = xy
        return Vec2d(cx-x+sx, cy-y+sy)

    def screen_to_world(self, xy):
        cx,cy = self.rect.center
        sx,sy = State.screen.rect.center
        x,y = xy
        return Vec2d(sx-x+cx, sy-y+cy)

    @property
    def visible_tile_range(self):
        tile_x,tile_y = State.tile_size
        (l,t),(r,b) = self.rect.topleft,self.rect.bottomright
        left = int(round(float(l) / tile_x - 1))
        right = int(round(float(r) / tile_x + 2))
        top = int(round(float(t) / tile_y - 1))
        bottom = int(round(float(b) / tile_y + 2))
        return left,top,right,bottom

    @property
    def visible_tiles(self):
        return State.map.get_tiles(*self.visible_tile_range)
