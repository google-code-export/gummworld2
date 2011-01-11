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


"""07_tiled_map.py - An example of using Tiled maps in Gummworld2.

This demo uses small tiles from a tileset distributed with Tiled 0.7.2, the
Java version. They are 32x32 pixels. For better performance one will want to
use larger tiles. See 09_collapse_map.py for a small-to-large tile conversion
demo.

Thanks to the creators of Tiled Map Editor:
    http://www.mapeditor.org/

Thanks to dr0id for his nice tiledtmxloader module:
    http://www.pygame.org/project-map+loader+for+%27tiled%27-1158-2951.html
"""


import pygame
from pygame.sprite import Sprite
from pygame.locals import (
    FULLSCREEN,
    Color,
    K_ESCAPE, K_g, K_l,
)

import paths
from gamelib import *


class Avatar(CameraTargetSprite):
    
    def __init__(self, map_pos, screen_pos):
        super(Avatar, self).__init__()
        self.image = pygame.surface.Surface((10,10))
        self.rect = self.image.get_rect()
        pygame.draw.circle(self.image, Color('yellow'), self.rect.center, 4)
        self.image.set_colorkey(Color('black'))
        self.position = map_pos
        self.screen_position = screen_pos


class App(Engine):
    
    def __init__(self, resolution=(640,480)):
        
        resolution = Vec2d(resolution)
        
        super(App, self).__init__(
            caption='07 Tiled Map -  G: grid | L: labels',
            camera_target=Avatar((325,420), resolution//2),
            resolution=resolution,
            frame_speed=0)
        
        ## Load Tiled TMX map, then update the world's dimensions. Really, all
        ## there is to it. See the toolkit module for more detail.
        State.map = toolkit.load_tiled_tmx_map('Gumm no swamps.tmx')
        State.world.rect = State.map.rect.copy()
        
        # I like huds.
        toolkit.make_hud()
        State.show_hud = True
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = Vec2d(State.camera.rect.size) // 2
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        # Mouse and movement state. move_to is in world coordinates.
        self.move_to = None
        self.speed = None
        self.target_moved = (0,0)
        self.mouse_down = False
        
    def update(self):
        """overrides Engine.update"""
        # If mouse button is held down update for continuous walking.
        if self.mouse_down:
            self.update_mouse_movement(pygame.mouse.get_pos())
        self.update_camera_position()
        State.camera.update()
        State.hud.update()
        
    def update_mouse_movement(self, pos):
        # Angle of movement.
        angle = geometry.angle_of(self.speed_box.center, pos)
        # Final destination.
        self.move_to = None
        for edge in self.speed_box.edges:
            # line_intersects_line() returns False or (True,(x,y)).
            cross = geometry.line_intersects_line(edge, (self.speed_box.center, pos))
            if cross:
                x,y = cross[1]
                self.move_to = State.camera.screen_to_world(pos)
                self.speed = geometry.distance(
                    self.speed_box.center, (x,y)) / self.max_speed_box
                break
        
    def update_camera_position(self):
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
            camera.position = wx,wy
        
    def draw(self):
        """overrides Engine.draw"""
        # Draw stuff.
        State.camera.interpolate()
        State.screen.clear()
        toolkit.draw_tiles()
        toolkit.draw_grid()
        toolkit.draw_labels()
        State.hud.draw()
        self.draw_avatar()
        State.screen.flip()
        
    def draw_avatar(self):
        camera = State.camera
        avatar = camera.target
        camera.surface.blit(avatar.image, avatar.screen_position)
        
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
            quit()
        
    def on_quit(self):
        quit()


if __name__ == '__main__':
    app = App()
    app.run()
