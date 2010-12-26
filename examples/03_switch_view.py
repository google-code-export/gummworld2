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


__version__ = '0.2'
__vernum__ = (0,2)


"""map_editor.py - An example of switching state in Gummworld2.

This example has two views: a full-window view and a sub-window view. Use TAB to
switch between them. This example only uses the State tricks to swap two
cameras, but with a little care any objects stored in State can be managed in
this fashion.

Look at the special comments in App.__init__() and App.on_key_down() for setting
this up and using it.

Also, see State.restore() and Camera.state_restored() for some special comments
about fashioning an object to be sensitive to its state being restored.
"""


import pygame
from pygame.locals import K_TAB, K_UP, K_DOWN, K_LEFT, K_RIGHT
import pymunk

import paths
from gamelib import *


class App(Engine):
    
    def __init__(self):
        super(App, self).__init__(frame_speed=0)
        
        pygame.display.set_caption('Press TAB to cycle views')
        
        ## Save the main state.
        State.save('main')
        
        ## Make a significant change to the state, then save it under a
        ## different name.
        
        # The rect that defines the screen subsurface. It will also be used to
        # draw a border around the subsurface.
        self.view_rect = pygame.Rect(33,33,500,500)
        
        # Set up the subsurface as the camera's drawing surface.
        subsurface = State.screen.surface.subsurface(self.view_rect)
        State.camera = Camera(State.world.avatar,
            subsurface, subsurface.get_rect())
        State.name = 'small'
        State.save(State.name)
        
        ## Easy way to select the "next" state name.
        self.next_state = {
            'main' : 'small',
            'small' : 'main',
        }
        
        # Make some default content.
        toolkit.make_tiles()
        
        self.move_x = 0
        self.move_y = 0
        
    def update(self):
        """overrides Engine.update"""
        self.update_avatar_position()

    def draw(self):
        """overrides Engine.draw"""
        # Draw stuff.
        State.camera.interpolate()
        State.screen.clear()
        toolkit.draw_tiles()
        if State.name == 'small':
            pygame.draw.rect(State.screen.surface, (99,99,99), self.view_rect, 1)
        State.screen.flip()
        
    def update_avatar_position(self):
        """update the avatar's position if any movement keys are held down
        """
        if self.move_y or self.move_x:
            avatar = State.world.avatar
            wx,wy = avatar.position + (self.move_x,self.move_y)
            rect = State.world.rect
            wx = max(min(wx,rect.right), rect.left)
            wy = max(min(wy,rect.bottom), rect.top)
            avatar.position = wx,wy
        
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
        elif key == K_TAB:
            ## Select the next state name and and restore it.
            # Note that Camera class has a state_restored() method which is
            # called by State.restore(). If it did not, you would see strange
            # video behavior when swapping in a camera with stale innards. You
            # may need to do this for your own classes if you integrate them
            # with State.save() and State.restore().
            State.restore(self.next_state[State.name])
        
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
