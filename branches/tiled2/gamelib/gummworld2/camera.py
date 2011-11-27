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


__doc__="""
camera.py - Camera module for Gummworld2.
"""


import pygame

from gummworld2 import State, Map, MapLayer, TiledMap, SuperMap, Vec2d, geometry


class Camera(object):
    """A Camera provides a few services:
    
        * Track a moving target in world coordinates.
        * Convert coordinates between world and screen space.
        * Interpolated view scrolling to take advantage of higher frame rates.
    
    Dependencies:
    
        * A target with a Vec2d attribute target.position.
        * A surface from which to derive its viewing dimensions.
        * State.clock is needed by interpolate().
    
    To use the camera do the following:
        
        1.  In the game's update routine set camera.position to move the target.
        2.  Also in the game's update routine call Camera.update() to update the
            camera's state.
        3.  In the game's draw routine call Camera.interpolate() to micro-update
            the scrolling between the position prior to step 1 and final
            position specified in step 1. This may sound complicated, but it is
            all handled behind the scenes.
    
    Screen-to-world and world-to-screen conversions are used to convert between
    world coordinates and screen coordinates.
    
    Note that using mouse position can be tricky if the camera is using a
    subsurface of the screen, or an alternate surface. pygame always reports
    mouse position relative to the top-level surface. Keep this in mind when
    positioning graphics based on the mouse position under these circumstances.
    Sometimes it may just be simplest, for example, to blit directly to the
    top-level surface.
    
    If creating multiple cameras to save and restore in State contexts, by
    default the state_restored() method updates the new camera from the old.
    This solves a split-brain condition that occurs when the cameras' internals
    fall out of sync. In some scenarios you may want to have two independent
    cameras. To prevent them from syncing during a restore, set the cameras'
    update_when_restored=False.
    """
    
    def __init__(self, target, view=None):
        """Construct an instance of Camera.
        
        The target argument is the object that camera should track. target must
        have a position attribute which is its location in world coordinates.
        
        The view argument is the screen.View object upon which to base
        conversions between world and screen space. The view.surface attribute
        is exposed view the Camera.surface property.
        """
        if view is None:
            view = State.screen
        self._target = target
        self._prev_target = target
        self._move_to = Vec2d(self.target.position)
        self._move_from = Vec2d(self.target.position)
        self._position = Vec2d(self.target.position)
        self.view = view
        self.update_when_restored = True
    
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
        self._interp = 0.0
        
    @property
    def view(self):
        """The view from which to derive the surface and viewing dimensions and,
        for subsurfaces, the rect for the subsurface in the parent surface.
        """
        return self._view
    @view.setter
    def view(self, val):
        self._view = val
        self._init()
        
    @property
    def surface(self):
        """The surface from which to derive the viewing dimensions.
        """
        return self._surface
        
    def _init(self):
        """Automatically called after setting view.
        """
        self._surface = self.view.surface
        self.rect = self.surface.get_rect()
        
        # Offsets used in conversions
        self._abs_offset = Vec2d(self.surface.get_abs_offset())
        self._screen_center = self.rect.center
        self._abs_screen_center = Vec2d(self.rect.center) + self.abs_offset
        
        self._interp = 0.0
#        self._move_to = Vec2d(self.target.position)
#        self._move_from = Vec2d(self._move_to)
#        self._position = Vec2d(self._move_to)
        self.map = None
        self.update()
    
    def update(self, *args):
        """Update Camera internals to prepare for efficient interpolation.
        
        Call in the game's update routine after changing Camera.position.
        """
        self._position[:] = self._move_from[:] = self._move_to
        self._move_to[:] = self.target.position
    
    def interpolate(self, *args):
        """Interpolate camera position towards target for smoother scrolling
        
        After updating the target position in the main program's update(), call
        this every frame in the main program's draw() before any drawing
        commands. It works best when frame speed is much higher than update
        speed.
        """
        interp = State.clock.interpolate
        x,y = self._position[:] = geometry.interpolant_of_line(
            interp, self._move_from, self._move_to)
        self.rect.center = round(x),round(y)
        self._interp = interp
        return interp
    
    def slew(self, vec, dt):
        """Move Camera.target via pymunk.
        
        If using pymunk, use this instead of Camera.position.
        """
        self.target.slew(vec, dt)
    
    def init_position(self, pos):
        """Hard set position to pos.
        
        This circumvents interpolation, which may be desirable if for example
        setting the initial position of the camera, or moving the camera a
        great distance when you don't want it to pan.
        """
        tpos = self.target.position
        tpos.x,tpos.y = pos
        self._move_to[:] = self._move_from[:] = self._position[:] = pos
        self.interpolate()
    
    @property
    def position(self):
        """Move Camera.target in world coordinates.
        """
        return self.target.position
    @position.setter
    def position(self, val):
        self.target.position = val
    
    @property
    def anti_interp(self):
##        return self.target_moved * self.interp - self.target_moved
        pass
    
    @property
    def steady_target_position(self):
        """The camera target's position with factored interpolation.
        
        Use this to get the interpolated position of camera target. Note that
        this is different than interpolating a tile or free-roaming sprite,
        which scroll in the opposite direction of the camera target.
        
        Example:
            target_rect.center = camera.steady_target_position
            screen.blit(target_image, target_rect)
        
        Think of it as an alternative to hard-coding screen center:
            target_rect.center = 300,300
            screen.blit(target_image, target_rect)
        """
        x,y = self.position + self.anti_interp
        return round(x),round(y)
    
    @property
    def screen_center(self):
        """The coordinates of the camera surface's center.
        
        In general, this is typically useful in screen-map calculations.
        
        This is equivalent to camera.surface.get_rect().center. The value is
        cached whenever the camera.surface attribute is set.
        """
        return Vec2d(self._screen_center)
    
    @property
    def abs_screen_center(self):
        """The absolute coordinates of the camera surface's center.
    
        In general, this is typically useful in mouse-map calculations.
    
        This is equivalent to camera.surface.get_rect().center +
        camera.surface.abs_offset(). The value is cached whenever the
        camera.surface attribute is set.
        """
        return Vec2d(self._abs_screen_center)
    
    @property
    def abs_offset(self):
        """Offset position camera.subsurface inside its top level parent surface.
        
        This is equivalent to camera.surface.get_abs_offset(). The value is
        cached whenever the camera.surface attribute is set.
        """
        return Vec2d(self._abs_offset)
    
    def world_to_screen(self, xy):
        """Convert coordinates from world space to screen space.
        """
#        world = Vec2d(self.rect.center) - xy
#        return self.abs_screen_center - world
        cx,cy = self.rect.topleft
        x,y = xy
        return Vec2d(x-cx, y-cy)
        
    def screen_to_world(self, xy):
        """Convert coordinates from screen space to world space.
        """
        camera = self.target.position
        ## ?? this should be relative to subsurface ??
        return xy + camera - self.abs_screen_center
    
    def state_restored(self, prev):
        """Sync a stale camera after swapping it in.
        
        If switching states either manually, you may want to call this to
        avoid video flashing or whizzing by. This typically happens when using
        Camera.interpolate() and swapping in the old camera, which has stale
        values in the _move_to and _move_from attributes. When swapping a camera
        in via State.restore(), this method is called automatically.
        """
        if self.update_when_restored and prev is not self:
            self.rect.center = prev.rect.center
            self._interp = prev._interp
            self._move_from = prev._move_from
            self._move_to = prev._move_to
            self._position = prev._position
