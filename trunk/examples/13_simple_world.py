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


"""12_separate_model_and_view.py - An example of separating model and view in
Gummworld2.

This uses the dumb model.World class to store model objects.
"""


from random import randrange, choice

import pygame
from pygame.locals import Color, K_SPACE, K_UP, K_DOWN, K_LEFT, K_RIGHT

import paths
from gamelib import *


def make_image(color, size):
    image = pygame.surface.Surface(size)
    if not isinstance(color, Color):
        color = Color(color)
    image.fill(color)
    return image


class Thing(model.Object):
    
    def __init__(self, color_name, size):
        super(Thing, self).__init__()
        self.color = color_name
        self.size = size
        self.rect = pygame.Rect(0,0,*size)
        self._position = Vec2d(0.0,0.0)
        rr = randrange
        world_rect = State.world.rect
        self.position = rr(world_rect.width), rr(world_rect.height)
        self.rect.clamp_ip(world_rect)
        self.position = self.rect.center
        self.dir = Vec2d(choice([-5.0,5.0]), choice([-5.0,5.0]))
        self.half_size = Vec2d(size[0]//2, size[1]//2)
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        p = self._position
        p.x,p.y = float(val[0]),float(val[1])
        self.rect.center = int(round(p.x)), int(round(p.y))
    
    def update(self, *args):
        dir = self.dir
        self.position += dir
        rect = self.rect
        world_rect = State.world.rect
        dx,dy = 1,1
        if rect.x < 0 or rect.right >= world_rect.right:
            dx = -1
        if rect.y < 0 or rect.bottom >= world_rect.bottom:
            dy = -1
        if (dx,dy) != (1,1):
            self.position -= dir
            dir.x,dir.y = dir.x*dx,dir.y*dy
            self.position += dir


class App(Engine):
    
    def __init__(self):
        
        super(App, self).__init__(
            caption='01 Full Window',
            frame_speed=0,
            world_type=SIMPLE_WORLD)
        
        # Make some default content.
        toolkit.make_tiles2()
        
        # Model some things.
        thing_size = 30,30
        self.things = []
        for color in ('red','blue','yellow'):
            for i in range(10):
                thing = Thing(color, (thing_size))
                self.things.append(thing)
                State.world.add(thing)
        
        # Make some images.
        self.images = {}
        for color in ('red','blue','yellow'):
            self.images[color] = make_image(color, (thing_size))
        
        # Display mode.
        self.wireframe = True
        
        # Hold cursor key-down states.
        self.move_x = 0
        self.move_y = 0
        
    def update(self):
        """overrides Engine.update"""
        self.update_camera_position()
        State.camera.update()
        for thing in self.things:
            thing.update()

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
        State.camera.interpolate()
        State.screen.clear()
        toolkit.draw_tiles()
        self.draw_scene()
        State.screen.flip()
        
    def draw_scene(self):
        surf = State.camera.surface
        images = self.images
        interp = State.camera.interp
        if self.wireframe:
            for frame in [f for f in State.world.objects() if isinstance(f, Thing)]:
                rect = frame.rect.copy()
                pos = State.camera.world_to_screen(frame.rect.center)
                pos = toolkit.interpolated_step(pos, frame.dir, interp)
                rect.center = round(pos.x),round(pos.y)
                pygame.draw.rect(surf, Color(frame.color), rect, 1)
        else:
            for frame in [f for f in State.world if isinstance(f, Thing)]:
                rect = frame.rect.copy()
                pos = State.camera.world_to_screen(frame.rect.center)
                pos = toolkit.interpolated_step(pos, frame.dir, interp)
                rect.center = round(pos.x),round(pos.y)
                surf.blit(images[frame.color], rect)
    
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        if key == K_DOWN:
            self.move_y += State.speed
        elif key == K_UP:
            self.move_y -= State.speed
        elif key == K_RIGHT:
            self.move_x += State.speed
        elif key == K_LEFT:
            self.move_x -= State.speed
        elif key == K_SPACE:
            self.wireframe = not self.wireframe
        
    def on_key_up(self, key, mod):
        # Turn off key-presses.
        if key == K_DOWN:
            self.move_y -= State.speed
        elif key == K_UP:
            self.move_y += State.speed
        elif key == K_RIGHT:
            self.move_x -= State.speed
        elif key == K_LEFT:
            self.move_x += State.speed
            self.move_x = 0
        
    def on_quit(self):
        quit()


if __name__ == '__main__':
    app = App()
    app.run()
