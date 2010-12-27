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

from gamelib import State, Vec2d


class Camera(object):
    
    def __init__(self, target, surface):
        self._target = target
        self._surface = surface
        self._init()
    
    @property
    def target(self):
        return self._target
    @target.setter
    def target(self, val):
        self._target = val
        self.update()
    
    @property
    def surface(self):
        return self._surface
    @surface.setter
    def surface(self, val):
        self._surface = val
        self._init()
    
    def _init(self):
        """must be called after setting surface
        """
        self.rect = self.surface.get_rect()
        
        # Offsets used in conversions
        self.abs_offset = Vec2d(self.surface.get_abs_offset())
        self.screen_offset = Vec2d(self.rect.center) - self.rect.topleft + self.abs_offset
        
        self._move_from = Vec2d(self.target.position)
        self._move_to = Vec2d(self.target.position)
        self._interp = 0.0
        self.update()
        
    def interpolate(self):
        """interpolate camera position towards target for smoother scrolling
        
        You typically want to use this or Camera.update(), not both.
        
        After updating the target position in the main program's update(), call
        this every frame in the main program's draw() before any drawing
        commands. It works best when frame speed is much higher than update
        speed.
        """
        target_pos = self.target.position
        if self._move_from != target_pos:
            interp = State.clock.interpolate()
            if interp < self._interp:
                # camera has caught up with target
                self._move_from = self._move_to
                self._interp = 0.0
            else:
                # camera must catch up with target
                x1,y1 = self._move_from
                x2,y2 = target_pos
                x = x1 + (x2-x1) * interp
                y = y1 + (y2-y1) * interp
                self.rect.center = int(round(x)), int(round(y))
                self._interp = interp
        if self._move_to != target_pos:
            self._move_from = self._move_to
            self._move_to = Vec2d(target_pos)
        
    def update(self):
        """relocate camera position immediately to target
        
        You typically want to use this or Camera.interpolate(), not both.
        """
        v = self.target.position
        v = int(round(v.x)), int(round(v.y))
        if self.rect.center != v:
            self.rect.center = v
        
    def state_restored(self):
        """If switching states either manually or via State.save() and
        State.restore(), you may want to call this to avoid video flashing or
        whizzing by. This typically happens when using Camera.interpolate() and
        swapping in the old camera, which has stale values in the _move_to and
        _move_from attributes.
        """
        self.update()
        self._move_to = self._move_from = Vec2d(self.target.position)
        
    @property
    def position(self):
        return self.target.position
        
    @property
    def screen_position(self):
        return self.world_to_screen(self.world_position)
        
    def world_to_screen(self, xy):
        """convert world space to screen space
        """
        world = self.target.position - xy
        return self.screen_offset - world
        
    def screen_to_world(self, xy):
        """convert screen space to world space
        """
        camera = self.target.position
        return xy + camera - self.screen_offset
        
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
