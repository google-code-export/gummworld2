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


"""10_minimap.py - An example using sub-window as a minimap for Gummworld2.

This demonstrates accessing Screen, Camera and World to convert their dimensions
for a particular use.

It also demonstrates use of BucketSprite and BucketGroup, two classes that work
together in Gummworld2 to manage sprites in the traditional pygame manner.

And throw in interpolated stepping for the moving balls (lines 190-191 in
App.draw_balls()). Interpolation is expensive when used on a high number of
objects, but without it the balls' movement is unpleasantly jerky because of the
5-pixel step that occurs at each update.
"""


from random import randrange, choice

import pygame
from pygame.locals import Color, K_UP, K_DOWN, K_LEFT, K_RIGHT

import paths
from gamelib import *


class Sprite(BucketSprite):
    """A fast moving square of random color."""
    
    def __init__(self):
        super(Sprite, self).__init__()
        self.image = pygame.surface.Surface((10,10))
        rr = randrange
        color = Color(rr(128,255), rr(128,255), rr(128,255), rr(128,255))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        world_rect = State.world.rect
        self.position = rr(world_rect.width), rr(world_rect.height)
        self.dir = Vec2d(choice([-5.0,5.0]), choice([-5.0,5.0]))
    
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
        self.mini_screen = Surface(
            State.screen.surface, pygame.Rect(475,25,100,100))
        
        # tiny_rect will be drawn on the minimap to indicate the visible area of
        # the world (the screen, aka camera).
        self.tiny_rect = self.mini_screen.rect.copy()
        size = Vec2d(State.screen.size)
        size.x = float(size.x)
        size.y = float(size.y)
        size = size / State.world.rect.size * self.mini_screen.rect.size
        self.tiny_rect.size = round(size.x),round(size.y)
        
        # A dot represents a full sprite on the minimap.
        self.dot = pygame.surface.Surface((1,1))
        self.dot.fill(Color('white'))
        
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
        dot = self.dot
        for s in sprite_group:
            pos = s.rect.topleft / full_size * mini_size
            mini_surf.blit(dot, (round(pos.x), round(pos.y)))
        
        # Draw a border.
        pygame.draw.rect(State.screen.surface, (99,99,99),
            mini_screen.super_rect.inflate(2,2), 1)


class App(Engine):
    
    def __init__(self):
        self.caption = '10 Minimap'
        super(App, self).__init__(
            caption=self.caption,
            resolution=(600,600),
            frame_speed=0)
        
        # Set up the minimap.
        self.minimap = Minimap()
        
        # Make some default content.
        toolkit.make_tiles()
        map = State.map
        self.sprite_group = BucketGroup(map.tile_size, map.map_size)
        for i in range(50):
            self.sprite_group.add(Sprite())
        
        State.camera.position = 300,300
        
        self.move_x = 0
        self.move_y = 0
        
    def update(self):
        """overrides Engine.update"""
        self.update_camera_position()
        State.camera.update()
        self.sprite_group.update()
        if State.clock.interpolate() < 0.1:
            pygame.display.set_caption(self.caption+' - %d fps' % State.clock.get_fps())

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
        
    def draw(self):
        """overrides Engine.draw"""
        # Draw stuff.
        self.interp = State.camera.interpolate()
        State.screen.clear()
        toolkit.draw_tiles()
        self.draw_balls()
        self.minimap.draw(self.sprite_group)
        State.screen.flip()
        
    def draw_balls(self):
        # Balls move pretty fast, so we'll interpolate their movement to smooth
        # out the motion.
        camera = State.camera
        camera_pos = Vec2d(camera.rect.topleft)
        interp = self.interp
        # Draw visible sprites...
        for s in self.sprite_group.sprites_in_range(
            State.camera.visible_tile_range[0]):
            x,y = toolkit.interpolated_step(
                s.rect.topleft-camera_pos, s.dir, interp)
            camera.surface.blit(s.image, (round(x),round(y)))
    
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
        
    def on_key_up(self, key, mod):
        # Turn off key-presses.
        if key in (K_DOWN,K_UP):
            self.move_y = 0
        elif key in (K_RIGHT,K_LEFT):
            self.move_x = 0
        
    def on_quit(self):
        quit()


if __name__ == '__main__':
    app = App()
    app.run()
