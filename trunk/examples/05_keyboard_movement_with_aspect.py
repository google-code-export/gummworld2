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


"""05_keyboard_movement_with_aspect.py - An example of using movement aspect in
Gummworld2.
"""


import pygame
from pygame.locals import K_TAB, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_ESCAPE

import paths
from gamelib import *


class App(Engine):
    
    def __init__(self):
        ## Make tiles wider than they are high to an give illusion of depth.
        ## This is not necessary for the effect, as the scrolling suggests more
        ## playfield is visible along the y-axis. However, if the tiling pattern
        ## is visible a "squat" appearance to the tiles can add to the effect.
        super(App, self).__init__(
            caption='05 Keyboard Movement with Aspect - Press TAB to cycle views',
            tile_size=(128,64), map_size=(10,20), frame_speed=0)

        ## Map scrolls 1.0X on x-axis, 0.5X on y-axis. See on_key_down() for the
        ## application of these values. The net visual effect is that the map
        ## scrolls slower along the y-axis than the x-axis.
        self.aspect = Vec2d(1.0, 0.5)

        # Save the main state.
        State.save('main')
        
        # The rect that defines the screen subsurface. It will also be used to
        # draw a border around the subsurface.
        self.view_rect = pygame.Rect(30,20,500,500)
        
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
        State.show_labels = True
        
        self.move_x = 0
        self.move_y = 0
        
        ## Warp avatar to center map.
        State.camera.target.position = State.world.rect.center
        State.camera.update()
        
    def update(self):
        """overrides Engine.update"""
        self.update_camera_position()
        State.camera.update()
        State.hud.update()
        
    def draw(self):
        """overrides Engine.draw"""
        # Draw stuff.
        State.camera.interpolate()
        State.screen.clear()
        toolkit.draw_tiles()
        toolkit.draw_labels()
        State.hud.draw()
        if State.name == 'small':
            pygame.draw.rect(State.screen.surface, (99,99,99), self.view_rect, 1)
        State.screen.flip()
        
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
        
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        ## Factor X and Y aspect into speed.
        if key == K_DOWN:
            self.move_y = 1 * State.speed * self.aspect.y
        elif key == K_UP:
            self.move_y = -1 * State.speed * self.aspect.y
        elif key == K_RIGHT:
            self.move_x = 1 * State.speed * self.aspect.x
        elif key == K_LEFT:
            self.move_x = -1 * State.speed * self.aspect.x
        elif key == K_TAB:
            # Select the next state name and and restore it.
            State.restore(self.next_state[State.name])
        elif key == K_ESCAPE:
            quit()
        
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
