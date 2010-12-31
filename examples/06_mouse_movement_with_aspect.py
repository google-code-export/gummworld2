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
from pygame.locals import (
    FULLSCREEN,
    Color, K_TAB, K_ESCAPE, K_g, K_l,
)

import paths
from gamelib import *


class App(Engine):
    
    def __init__(self):
        ## Make tiles wider than they are high to an give illusion of depth.
        ## This is not necessary for the effect, as the scrolling suggests more
        ## playfield is visible along the y-axis. However, if the tiling pattern
        ## is visible a "squat" appearance to the tiles can add to the effect.
        super(App, self).__init__(
            caption='06 Mouse Movement with Aspect - TAB: view | G: grid | L: labels',
            resolution=(640,480),
            ##display_flags=FULLSCREEN,
            tile_size=(128,64), map_size=(10,20), frame_speed=0)

        # Save the main state.
        State.save('main')
        
        # The rect that defines the screen subsurface. It will also be used to
        # draw a border around the subsurface.
        size = (State.screen.width*3/4, State.screen.height*3/4)
        self.view_rect = pygame.Rect(30,20,*size)
        
        # Set up the subsurface as the alternate camera's drawing surface.
        subsurface = State.screen.surface.subsurface(self.view_rect)
        State.camera = Camera(State.camera.target, subsurface)
        State.name = 'small'
        State.save(State.name)
        
        # Easy way to select the "next" state name.
        self.next_state = {
            'main' : 'small',
            'small' : 'main',
        }
        
        # Make some default content.
        toolkit.make_tiles2()
        toolkit.make_hud()
        State.show_hud = True
        
        # Warp avatar to center map.
        State.camera.target.position = State.world.rect.center
        State.camera.update()
        
        ## Mouse movement is going to use a diamond geometry to calculate a
        ## speed factor that's derived from the distance from center to the
        ## edge. Max speed will be horizontal; min speed will be vertical.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = self.view_rect.center
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        ## move_to is world coordinates.
        self.move_to = None
        self.speed = None
        self.mouse_down = False

    def update(self):
        """overrides Engine.update"""
        ## If mouse button is held down update for continuous walking.
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
        ## Speed box center is screen center, this is the origin. Mouse pos is
        ## the other end point, which makes a line. Start by getting the angle
        ## of the line.
        angle = geometry.angle_of(self.speed_box.center, pos)
        ## Loop through all the diamond sides. Test if the line made by the
        ## mouse intersects with an edge. If not, then we're done because the
        ## mouse clicked inside the (very small) diamond.
        self.move_to = None
        for edge in self.speed_box.edges:
            # lines_intersection() returns (True,True) or (False,False) if there
            # is no intersection.
            x,y = geometry.lines_intersection(edge, (self.speed_box.center, pos))
            if x not in (True,False):
                self.move_to = State.camera.screen_to_world(pos)
                break
        ## If we have an intersect point, we can get the distance from the
        ## screen center (where the avatar is) and the intersect point. By
        ## coincidence this distance scales exactly like we want it to based on
        ## the angle being more vertical or more horizontal.
        if self.move_to is not None:
            self.speed = geometry.distance(
                self.speed_box.center, (x,y)) / self.max_speed_box
        self.mouse_down = True
        
    def update_avatar_position(self):
        """update the avatar's position if any movement keys are held down
        """
        if self.move_to is not None:
            avatar = State.camera.target
            wx,wy = avatar.position
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
            avatar.position = wx,wy
        
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
