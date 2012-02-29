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


"""08_pymunk_motion.py - An example of using pymunk motion in Gummworld2.

The Camera.target is a pymunk.Body object. The pymunk API is used for motion.

This demo uses small tiles from a tileset distributed with Tiled 0.7.2, the
Java version. They are 32x32 pixels. For better performance one will want to
use larger tiles. See 09_collapse_map.py for a small-to-large tile conversion
demo.
"""


import pygame
from pygame.sprite import Sprite
from pygame.locals import *
try:
    import pymunk
except:
    print 'This demo requires pymunk'
    quit()

import paths
import gummworld2
from gummworld2 import context, data, model, geometry, toolkit
from gummworld2 import Engine, State, TiledMap, Vec2d


class Avatar(model.Object):
    
    def __init__(self, screen_pos):
        model.Object.__init__(self)
        self.image = pygame.Surface((10,10))
        self.rect = self.image.get_rect()
        pygame.draw.circle(self.image, Color('yellow'), self.rect.center, 4)
        self.rect.center = screen_pos
        self.image.set_colorkey(Color('black'))


class App(Engine):
    
    def __init__(self, resolution=(640,480)):
        
        resolution = Vec2d(resolution)
        
        # Load Tiled TMX map, then update the world's dimensions.
        tiled_map = TiledMap(data.filepath('map', 'Gumm no swamps.tmx'))
        
        ## Camera target is a pymunk circle body. We want to delay scheduling
        ## the world and camera items until after we create the world.
        Engine.__init__(self,
            caption='08 pymunk Motion -  G: grid | L: labels',
            resolution=resolution,
            map=tiled_map, world_type=gummworld2.PYMUNK_WORLD,
            frame_speed=0)  #, default_schedules=False)
        
        self.visible_objects = []
        
        # Make an avatar sprite so we have something to draw.
        self.avatar = Avatar(resolution//2)
        
        # I like huds.
        toolkit.make_hud()
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = Vec2d(State.camera.rect.size) // 2
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        # Mouse and movement state. move_to is in world coordinates.
        self.move_to = None
        self.speed = None
        self.mouse_down = False
        
        self.grid_cache = {}
        self.label_cache = {}
        
        State.camera.init_position((325,420))
    
    def update(self, dt):
        """overrides Engine.update"""
        # If mouse button is held down update for continuous walking.
        if self.mouse_down:
            self.update_mouse_movement(pygame.mouse.get_pos())
        self.update_camera_position(dt)
        State.camera.update()
        State.world.step(dt)
        self.visible_objects = toolkit.get_object_array()
        State.hud.update(dt)
    
    def update_mouse_movement(self, pos):
        # Angle of movement.
        angle = geometry.angle_of(self.speed_box.center, pos)
        # Final destination.
        self.move_to = None
        for edge in self.speed_box.edges:
            # line_intersects_line() returns False or (True,(x,y)).
            cross = geometry.line_intersects_line(edge, (self.speed_box.center, pos))
            if cross:
                x,y = cross[0]
                self.move_to = State.camera.screen_to_world(pos)
                self.speed = geometry.distance(
                    self.speed_box.center, (x,y)) / self.max_speed_box
                break
    
    def update_camera_position(self, dt):
        """update the camera's position if any movement keys are held down
        """
        if self.move_to is not None:
            camera = State.camera
            wx,wy = camera.position
            # Speed formula.
            speed = self.speed * State.speed
            # If we're within spitting distance, then taking a full step would
            # overshoot the desired destination. Therefore, we'll jump there.
            if geometry.distance((wx,wy), self.move_to) < speed:
                wx,wy = self.move_to
                self.move_to = None
            else:
                # Otherwise, calculate the full step.
                angle = geometry.angle_of((wx,wy), self.move_to)
                wx,wy = geometry.point_on_circumference((wx,wy), speed, angle)
            # Keep avatar inside map bounds.
            rect = State.world.rect
            wx = max(min(wx,rect.right), rect.left)
            wy = max(min(wy,rect.bottom), rect.top)
            camera.slew(Vec2d(wx,wy), dt)
        elif State.camera.target.velocity != (0,0):
            State.camera.target.velocity = (0,0)
    
    def draw(self, dt):
        """overrides Engine.draw"""
        # Draw stuff.
        State.screen.clear()
        toolkit.draw_object_array(self.visible_objects)
        if State.show_grid:
            toolkit.draw_grid(self.grid_cache)
        if State.show_labels:
            toolkit.draw_labels(self.label_cache)
        State.hud.draw()
        self.draw_avatar()
        State.screen.flip()
    
    def draw_avatar(self):
        avatar = self.avatar
        State.camera.surface.blit(avatar.image, avatar.rect)
    
    def on_mouse_button_down(self, pos, button):
        self.mouse_down = True
    
    def on_mouse_button_up(self, pos, button):
        self.mouse_down = False
    
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        if key == K_g:
            State.show_grid = not State.show_grid
        elif key == K_l:
            State.show_labels = not State.show_labels
        elif key == K_ESCAPE:
            context.pop()
    
    def on_quit(self):
        context.pop()


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
