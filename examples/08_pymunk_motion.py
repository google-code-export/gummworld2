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


"""08_pymunk_motion.py - An example of using pymunk motion in Gummworld2.

The Camera.target is a pymunk.Body object. The pymunk API is used for motion.

This demo uses small tiles from a tileset distributed with Tiled 0.7.2, the
Java version. They are 32x32 pixels. For better performance one will want to
use larger tiles. See 09_collapse_map.py for a small-to-large tile conversion
demo.
"""


import pygame
from pygame.sprite import Sprite
from pygame.locals import (
    FULLSCREEN,
    Color,
    K_TAB, K_ESCAPE, K_g, K_l,
)
try:
    import pymunk
except:
    print 'This demo requires pymunk'
    quit()

import paths
from gamelib import *


class App(Engine):
    
    def __init__(self, resolution=(640,480)):
        super(App, self).__init__(
            caption='08 pymunk Motion -  TAB: view | G: grid | L: labels',
            camera_target=model.CircleBody(),
            resolution=resolution,
            ##display_flags=FULLSCREEN,
            frame_speed=0,
            use_pymunk=True)
        
        ## Load Tiled TMX map, then update the world and camera. Really, all
        ## there is to it. See the toolkit module for more detail.
        State.map = toolkit.load_tiled_tmx_map('Gumm no swamps.tmx')
        State.world.rect = State.map.rect.copy()
        
        # Save the main state.
        State.save('main')
        
        # The rect that defines the screen subsurface. It will also be used to
        # draw a border around the subsurface.
        self.view_rect = pygame.Rect(30,20,*State.screen.size*2//3)
        
        # Set up the subsurface as the camera's drawing surface.
        subsurface = State.screen.surface.subsurface(self.view_rect)
        State.camera = Camera(State.camera.target, subsurface)
        State.name = 'small'
        State.save(State.name)
        
        # Easy way to select the "next" state name.
        self.next_state = {
            'main' : 'small',
            'small' : 'main',
        }
        
        # I like huds.
        toolkit.make_hud()
        State.show_hud = True
        
        # Warp avatar to location on map.
        State.camera.target.position = 260,420
        State.camera.update()
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = self.view_rect.center
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        # Mouse and movement state. move_to is in world coordinates.
        self.move_to = None
        self.speed = None
        self.mouse_down = False
        
    def update(self):
        """overrides Engine.update"""
        # If mouse button is held down update for continuous walking.
        if self.mouse_down:
            self.update_mouse_movement(pygame.mouse.get_pos())
        self.update_avatar_position()
        State.hud.update()
        
    def draw(self):
        """overrides Engine.draw"""
        # Draw stuff.
        State.camera.interpolate()
        State.screen.clear()
        toolkit.draw_tiles()
        toolkit.draw_grid()
        toolkit.draw_labels()
        State.hud.draw()
        avatar_location = State.camera.world_to_screen(State.camera.position)
        pygame.draw.circle(State.screen.surface,
            Color('yellow'), avatar_location, 4)
        if State.name == 'small':
            pygame.draw.rect(State.screen.surface, (99,99,99), self.view_rect, 1)
        State.screen.flip()
        
    def update_mouse_movement(self, pos):
        # Angle of movement.
        angle = geometry.angle_of(self.speed_box.center, pos)
        # Final destination.
        self.move_to = None
        for edge in self.speed_box.edges:
            # lines_intersection() returns (True,True) or (False,False) if there
            # is no intersection.
            x,y = geometry.lines_intersection(edge, (self.speed_box.center, pos))
            if x not in (True,False):
                self.move_to = State.camera.screen_to_world(pos)
                break
        # Speed of movement.
        if self.move_to is not None:
            self.speed = geometry.distance(
                self.speed_box.center, (x,y)) / self.max_speed_box
        
    def update_avatar_position(self):
        """update the avatar's position if any movement keys are held down
        """
        if self.move_to is not None:
            avatar = State.camera.target
            wx,wy = avatar.position
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
            avatar.slew(Vec2d(wx,wy), State.dt)
        elif State.camera.target.velocity != (0,0):
            State.camera.target.velocity = (0,0)
        
    def on_mouse_button_down(self, pos, button):
        self.mouse_down = True
        
    def on_mouse_button_up(self, pos, button):
        self.mouse_down = False
        
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        if key == K_TAB:
            # Select the next state name and and restore it.
            State.restore(self.next_state[State.name])
            if State.name == 'small':
                self.speed_box.center = self.view_rect.center
            else:
                self.speed_box.center = State.screen.rect.center
        elif key == K_g:
            State.show_grid = not State.show_grid
        elif key == K_l:
            State.show_labels = not State.show_labels
        elif key == K_ESCAPE:
            quit()
        
    def on_quit(self):
        quit()


if __name__ == '__main__':
    app = App()
    app.run()
