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


__doc__="""
camera.py - Camera module for Gummworld2.
"""


import pygame

from gamelib import State, Vec2d


class Camera(object):
    """A Camera provides a few services:
    
        * Track a moving target in world coordinates.
        * Determine the range of visible tiles.
        * Retrieve visible tiles from a Map.
        * Convert coordinates between world and screen space.
        * Interpolated scrolling to take advantage of higher frame rates.
    
    Dependencies:
    
        * A target with a Vec2d attribute target.position.
        * A surface from which to derive its viewing dimensions.
        * State.clock is needed by interpolate().
    
    Simple usage is just a matter of updating the position of the target, and
    then calling Camera.update(). Both actions should occur during the clock's
    update cycle (Engine.update() if using Engine).
    
    Interpolated usage is as simple as updating the position of the target, and
    then calling Camera.interpolate(). The first action should be called in the
    clock's update cycle; the latter should be called in the clock's frame cycle
    (Engine.draw() if using Engine).
    
    Note that using mouse position can be tricky if the camera is using a
    subsurface of the screen, or an alternate surface. pygame always reports
    mouse position relative to the top-level surface. Keep this in mind when
    positioning graphics based on the mouse position under these circumstances.
    Sometimes it may just be simplest, for example, to blit directly to the
    top-level surface.
    """
    
    def __init__(self, target, surface):
        """Construct an instance of Camera.
        
        The target argument is the object that camera should track. target must
        have a position attribute which is its location in world coordinates.
        
        The surface argument is the pygame surface or subsurface upon which to
        base conversions between world and screen space.
        """
        self._target = target
        self._surface = surface
        self._init()
        
    @property
    def target(self):
        """The target that camera is tracking.
        """
        return self._target
    @target.setter
    def target(self, val):
        self._target = val
        self.update()
        
    @property
    def surface(self):
        """The surface from which to derive the viewing dimensions.
        """
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
        """Interpolate camera position towards target for smoother scrolling
        
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
        """Relocate camera position immediately to target.
        
        You typically want to use this or Camera.interpolate(), not both.
        """
        v = self.target.position
        v = int(round(v.x)), int(round(v.y))
        if self.rect.center != v:
            self.rect.center = v
        if self._move_from != v:
            self._move_from = Vec2d(v)
            self._move_to = Vec2d(v)
        
    def state_restored(self):
        """Sync a stale camera after swapping it in.
        
        If switching states either manually, you may want to call this to
        avoid video flashing or whizzing by. This typically happens when using
        Camera.interpolate() and swapping in the old camera, which has stale
        values in the _move_to and _move_from attributes. When swapping a camera
        in via State.restore(), this method is called automatically.
        """
        self.update()
        self._move_to = self._move_from = Vec2d(self.target.position)
        
    @property
    def position(self):
        """The camera's (target's) position in world coordinates.
        """
        return self.target.position
        
    @property
    def screen_position(self):
        """The camera's (target's) position in screen coordinates.
        """
        return self.world_to_screen(self.world_position)
        
    def world_to_screen(self, xy):
        """Convert coordinates from world space to screen space.
        """
        world = self.target.position - xy
        return self.screen_offset - world
        
    def screen_to_world(self, xy):
        """Convert coordinates from screen space to world space.
        """
        camera = self.target.position
        return xy + camera - self.screen_offset
        
    @property
    def visible_tile_range(self):
        """The range of tiles that would be visible on the display surface. The
        value is a tuple(x1,y1,x2,y2) representing map grid positions.
        """
        tile_x,tile_y = State.map.tile_size
        (l,t),(r,b) = self.rect.topleft,self.rect.bottomright
        left = int(round(float(l) / tile_x - 1))
        right = int(round(float(r) / tile_x + 2))
        top = int(round(float(t) / tile_y - 1))
        bottom = int(round(float(b) / tile_y + 2))
        return left,top,right,bottom
        
    @property
    def visible_tiles(self):
        """A 2D list of tiles that would be visible on the display surface.
        The first dimension is the map layer, the second is the tile. Tile lists
        are sorted in (column,row) order.
        """
        tile_range = self.visible_tile_range
        map = State.map
        get_tiles = map.get_tiles
        layer_range = range(len(map.layers))
        return [get_tiles(*tile_range, layer=n) for n in layer_range]
