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


"""06_mouse_movement_with_aspect.py - An example of using movement aspect in
Gummworld2.

This demo uses the mouse. There are a number of key points, since interpreting
the mouse state is a little more involved than key-presses. The demo handles
mouse-clicks, of course, and holding the mouse button down and dragging it for
continuous, dynamic movement.

Watch closely. As with the movement aspect demo involving key-presses, the map
scrolls faster horizontally than vertically. There is no real scenery in the
demo, but it may be possible to imagine a receding playfield along the Y axis.

Unlike the key-press demo, the scroll speed varies fractionally depending on
whether the mouse position is more vertical or horizontal.
"""


import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import Engine, State, CameraTargetSprite, Vec2d
from gummworld2 import context, geometry, toolkit


class Avatar(CameraTargetSprite):
    
    def __init__(self, map_pos, screen_pos):
        CameraTargetSprite.__init__(self)
        self.image = pygame.Surface((10,10))
        self.rect = self.image.get_rect()
        pygame.draw.circle(self.image, Color('yellow'), self.rect.center, 4)
        self.image.set_colorkey(Color('black'))
        self.position = map_pos
        self.screen_position = screen_pos


class App(Engine):
    
    def __init__(self):
        
        resolution = Vec2d(640,480)
        
        Engine.__init__(self,
            caption='06 Mouse Movement with Aspect - G: grid | L: labels',
            resolution=resolution,
            camera_target=Avatar((325,420), resolution//2),
            tile_size=(128,64), map_size=(10,20),
            frame_speed=0)
        
        # Make some default content.
        toolkit.make_tiles2()
        toolkit.make_hud()
        State.clock.schedule_update_priority(State.hud.update, 1.0)
        
        ## Mouse movement is going to use a diamond geometry to calculate a
        ## speed factor that's derived from the distance from center to the
        ## edge of the diamond at the angle to the mouse. Max speed will be
        ## horizontal; min speed will be vertical.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = Vec2d(State.camera.rect.size) // 2
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        ## move_to is world coordinates.
        self.move_to = None
        self.speed = None
        self.mouse_down = False
    
    def update(self, dt):
        """overrides Engine.update"""
        ## If mouse button is held down update for continuous walking.
        if self.mouse_down:
            self.update_mouse_movement(pygame.mouse.get_pos())
        self.update_camera_position()
    
    def update_mouse_movement(self, pos):
        ## Speed box center is screen center, this is the origin. Mouse pos is
        ## the other end point, which makes a line. Start by getting the angle
        ## of the line.
        angle = geometry.angle_of(self.speed_box.center, pos)
        ## Loop through all the diamond sides. Test if the line made by the
        ## mouse intersects with an edge. If not, then we're done because the
        ## mouse clicked inside the (very small) diamond.
        self.move_to = None
        for edge in self.speed_box.edges:
            ## line_intersects_line() returns False or (True,(x,y)).
            cross = geometry.line_intersects_line(edge, (self.speed_box.center, pos))
            if cross:
                x,y = cross[0]
                self.move_to = State.camera.screen_to_world(pos)
                self.speed = geometry.distance(
                    self.speed_box.center, (x,y)) / self.max_speed_box
                break
        self.mouse_down = True
    
    def update_camera_position(self):
        """update the camera's position if any movement keys are held down
        """
        if self.move_to is not None:
            camera = State.camera
            wx,wy = camera.position
            ## Avatar speed is product of the aspect calculation (from
            ## update_mouse_movement) and the global State.speed.
            speed = self.speed * State.speed
            ## If we're within spitting distance, then taking a full step would
            ## overshoot the desired destination. Therefore, we'll jump there.
            if geometry.distance((wx,wy), self.move_to) < speed:
                wx,wy = self.move_to
                self.move_to = None
            else:
                ## Otherwise, calculate the full step. Get the angle of the
                ## avatar and destination, then project a point at that angle
                ## and distance.
                angle = geometry.angle_of((wx,wy), self.move_to)
                wx,wy = geometry.point_on_circumference((wx,wy), speed, angle)
            # Keep avatar inside map bounds.
            rect = State.world.rect
            wx = max(min(wx,rect.right), rect.left)
            wy = max(min(wy,rect.bottom), rect.top)
            camera.position = wx,wy
    
    def draw(self, dt):
        """overrides Engine.draw"""
        # Draw stuff.
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
            context.pop()
    
    def on_quit(self):
        context.pop()


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
