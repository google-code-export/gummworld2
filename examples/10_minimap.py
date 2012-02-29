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


"""10_minimap.py - An example using sub-window as a minimap for Gummworld2.

This demonstrates accessing Screen, Camera and World to convert their dimensions
for a particular use.

And throw in interpolated stepping for the moving balls (lines 190-191 in
App.draw_balls()). Interpolation is expensive when used on a high number of
objects, but without it the balls' movement is unpleasantly jerky because of the
5-pixel step that occurs at each update.
"""


from random import randrange, choice

import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import Engine, State, BasicMap, SubPixelSurface, View, Vec2d
from gummworld2 import context, model, spatialhash, toolkit


class Sprite(object):
    """A fast moving square of random color."""
    
    def __init__(self):
        world_rect = State.world.rect
        rr = randrange
        self._position = Vec2d(rr(world_rect.width), rr(world_rect.height))
        
        self.image = pygame.Surface((10,10))
        color = Color(rr(128,255), rr(128,255), rr(128,255), rr(128,255))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=self.position)
        self.dir = Vec2d(choice([-5.0,5.0]), choice([-5.0,5.0]))
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        p = self._position
        p.x,p.y = val
        self.rect.center = round(p.x),round(p.y)
    
    def update(self):
        newx,newy = self.position + self.dir
        world_rect = State.world.rect
        if newx < 0 or newx >= world_rect.right:
            self.dir.x = -self.dir.x
        if newy < 0 or newy >= world_rect.bottom:
            self.dir.y = -self.dir.y
        self.position += self.dir


class Minimap(object):
    
    def __init__(self):
        
        # The minimap is a subsurface upon which the whole world is projected.
        self.mini_screen = View(
            State.screen.surface, pygame.Rect(475,25,100,100))
        
        # tiny_rect will be drawn on the minimap to indicate the visible area of
        # the world (the screen, aka camera).
        self.tiny_rect = self.mini_screen.rect.copy()
        size = Vec2d(State.screen.size)
        size.x = float(size.x)
        size.y = float(size.y)
        size = size / State.world.rect.size * self.mini_screen.rect.size
        self.tiny_rect.size = round(size.x),round(size.y)
        
        # A dot represents a full sprite on the minimap. SubPixelSurface is a
        # generated set of antialiased images that give the illusion of movement
        # smaller than one pixel. If we did not do this the dots would have an
        # annoying jerky movement.
        dot = pygame.surface.Surface((1,1))
        dot.fill(Color('white'))
        self.dot = SubPixelSurface(dot)
        
        # Pre-compute some reusable values.
        mini_screen = self.mini_screen
        mini_surf = mini_screen.surface
        mini_size = mini_screen.rect.size
        self.mini_size = mini_size
        
        full_size = Vec2d(State.world.rect.size)
        full_size.x = float(full_size.x)
        full_size.y = float(full_size.y)
        self.full_size = full_size

    def draw(self, sprite_group):
        mini_screen = self.mini_screen
        mini_surf = mini_screen.surface
        
        # Position the "visible area" tiny_rect, aka camera, within the minimap
        # so we can draw it as a filled rect.
        full_size = self.full_size
        mini_size = self.mini_size
        tiny_pos = State.camera.rect.topleft / full_size * mini_size
        self.tiny_rect.topleft = round(tiny_pos.x),round(tiny_pos.y)
        
        # Draw the minimap...
        mini_screen.clear()
        # Draw the camera area as a filled rect.
        pygame.draw.rect(mini_surf, Color(200,0,255), self.tiny_rect)
        # Draw sprites as dots.
        for s in sprite_group:
            pos = s.rect.topleft / full_size * mini_size
            dot = self.dot.at(pos.x, pos.y)
            mini_surf.blit(dot, pos, None, BLEND_RGBA_ADD)
        
        # Draw a border.
        pygame.draw.rect(State.screen.surface, (99,99,99),
            mini_screen.parent_rect.inflate(2,2), 1)


class App(Engine):
    
    def __init__(self):
        self.caption = '10 Minimap'
        super(App, self).__init__(
            caption=self.caption,
            resolution=(600,600),
            tile_size=(128,128), map_size=(10,10),
            frame_speed=0)
        
        # Set up the minimap.
        self.minimap = Minimap()
        
        # Make some default content.
        toolkit.make_tiles()
        map_ = State.map
        mw,mh = map_.width, map_.height
        tw,th = map_.tile_width, map_.tile_height
        self.balls = spatialhash.SpatialHash(map_.rect, 30)
        for i in range(50):
            self.balls.add(Sprite())
        
        self.visible_objects = []
        
        State.clock.schedule_interval(self.set_caption, 2.)
        
        self.move_x = 0
        self.move_y = 0
        
        State.camera.init_position(State.camera.rect.center - Vec2d(5,5))
        
    def update(self, dt):
        """overrides Engine.update"""
        self.update_camera_position()
        State.camera.update(dt)
        for ball in list(self.balls):
            ball.update()
            self.balls.add(ball)
        self.visible_objects = self.balls.intersect_objects(State.camera.rect)
    
    def update_camera_position(self):
        """update the camera's position if any movement keys are held down
        """
        if self.move_y or self.move_x:
            camera = State.camera
            wx,wy = camera.position + (self.move_x,self.move_y)
            rect = State.world.rect
            wx = max(min(wx,rect.right), rect.left)
            wy = max(min(wy,rect.bottom), rect.top)
            camera.position = wx,wy
    
    def set_caption(self, dt):
        pygame.display.set_caption(self.caption+' - %d fps' % State.clock.fps)
    
    def draw(self, dt):
        """overrides Engine.draw"""
        # Draw stuff.
        State.screen.clear()
        toolkit.draw_tiles()
        self.draw_balls()
        self.minimap.draw(self.balls)
        State.screen.flip()
        
    def draw_balls(self):
        # Balls move pretty fast, so we'll interpolate their movement to smooth
        # out the motion.
        camera = State.camera
        camera_pos = Vec2d(camera.rect.topleft)
        interp = State.camera.interp
        blit = camera.view.blit
        interpolated_step = toolkit.interpolated_step
        # Draw visible sprites...
        for s in self.visible_objects:
            x,y = interpolated_step(s.rect.topleft-camera_pos, s.dir, interp)
            blit(s.image, (round(x),round(y)))
    
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        if key == K_DOWN:
            self.move_y = 1 * State.speed
        elif key == K_UP:
            self.move_y = -1 * State.speed
        elif key == K_RIGHT:
            self.move_x = 1 * State.speed
        elif key == K_LEFT:
            self.move_x = -1 * State.speed
        elif key == K_ESCAPE:
            context.pop()
        
    def on_key_up(self, key, mod):
        # Turn off key-presses.
        if key in (K_DOWN,K_UP):
            self.move_y = 0
        elif key in (K_RIGHT,K_LEFT):
            self.move_x = 0
        
    def on_quit(self):
        context.pop()


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
