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


__version__ = '0.4'
__vernum__ = (0,4)


__doc__="""
camera.py - Camera module for Gummworld2.
"""


import pygame

from gamelib import State, MapLayer, Vec2d


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
        self._visible_tile_range = []
        self._visible_tiles = []
        self.target_moved = Vec2d(0,0)
        self._target_was_moved = False
        self._init()
        
    @property
    def interp(self):
        """The clock's interpolation value after the last call to
        Camera.interpolate.
        """
        return self._interp
    
    @property
    def target(self):
        """The target that camera is tracking.
        """
        return self._target
    @target.setter
    def target(self, val):
        self._target = val
        self._move_to = Vec2d(self.position)
        self._move_from = Vec2d(self.position)
        self._interp = 0.0
        
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
        self.map = None
        if State.map:
            self._get_visible_tile_range()
            self._get_visible_tiles()
        else:
            self._visible_tile_range = []
            self._visible_tiles = []
        self.update()
        
    def interpolate(self, sprites=None):
        """Interpolate camera position towards target for smoother scrolling
        
        You typically want to use this or Camera.update(), not both.
        
        After updating the target position in the main program's update(), call
        this every frame in the main program's draw() before any drawing
        commands. It works best when frame speed is much higher than update
        speed.
        """
        target_moved = self.target_moved
        interp = State.clock.interpolate()
        interpolated_step = target_moved - target_moved * interp
        x,y = self.target.position - interpolated_step
        self.rect.center = round(x), round(y)
        self._interp = interp
        
        if sprites:
            world_to_screen = self.world_to_screen
            for s in sprites:
                abs_screen_pos = world_to_screen(s.position)
                interpolated_step = target_moved - target_moved * interp
                x,y = abs_screen_pos + interpolated_step
                s.rect.center = round(x), round(y)
        
        return interp
    
    def update(self):
        """Relocate camera position immediately to target.
        
        You typically want to use this or Camera.interpolate(), not both.
        """
        target_was_moved = self._target_was_moved
        if target_was_moved == 1:
            self._target_was_moved = 0
        elif target_was_moved == 0:
            self.target_moved = Vec2d(0,0)
            self._target_was_moved = -1
        self._get_visible_tile_range()
        self._get_visible_tiles()
    
    def slew(self, vec, dt):
        """Move target via pymunk.
        
        If using pymunk, use this instead of Camera.position.
        """
        vec = Vec2d(vec)
        self._target_was_moved = 1
        self.target_moved = vec - self.target.position
        self.target.slew(vec, State.dt)
    
    @property
    def position(self):
        """The camera target's position in world coordinates.
        
        IMPORTANT: Call this instead of directly modifying the target object's
        position.
        """
        return self.target.position
    @position.setter
    def position(self, val):
        target = self.target
        self.target_moved = val - target.position
        target.position = val
        self._target_was_moved = 1
        
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
        value is a list of tuples(x1,y1,x2,y2) representing map grid positions
        for each layer. The per layer metrics are necessary because maps can
        have layers with different tile sizes, and therefore different grids.
        """
        return self._visible_tile_range
    
    def _get_visible_tile_range(self):
        range_per_layer = self._visible_tile_range
        del range_per_layer[:]
        for layeri,layer in enumerate(State.map.layers):
            tile_x,tile_y = layer.tile_size
            l,t,w,h = self.rect
            r = l+w
            b = t+h
            left = int(round(float(l) / tile_x)) - 1
            right = int(round(float(r) / tile_x)) + 2
            top = int(round(float(t) / tile_y)) - 1
            bottom = int(round(float(b) / tile_y)) + 2
            range_per_layer.append((left,top,right,bottom))
        
    @property
    def visible_tiles(self):
        """A 2D list of tiles that would be visible on the display surface.
        The first dimension is the map layer, the second is the tile. Tile lists
        are sorted in (column,row) order.
        """
        return self._visible_tiles
    
    def _get_visible_tiles(self):
        tile_per_layer = self._visible_tiles
        del tile_per_layer[:]
        tile_range = self.visible_tile_range
        map = State.map
        get_tiles = map.get_tiles
        for layeri,layer in enumerate(State.map.layers):
            tile_size,map_size,visible = layer.tile_size, layer.map_size, layer.visible
            new_layer = MapLayer(tile_size,map_size,visible)
            if visible:
                tiles = get_tiles(*tile_range[layeri], layer=layeri)
                new_layer.update([(tile.name,tile)
                    for tile in get_tiles(*tile_range[layeri], layer=layeri)
                ])
            tile_per_layer.append(new_layer)
    
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
