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
__author__ = 'Gummbum, (c) 2011-2013'


__doc__ = """03_switch_view.py - An example of switching state in Gummworld2.

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
from pygame.locals import K_ESCAPE, K_TAB, K_UP, K_DOWN, K_LEFT, K_RIGHT

import paths
import gummworld2
from gummworld2 import context, Engine, State, Camera, View, Vec2d, toolkit


class App(Engine):
    
    def __init__(self):
        ## Turn off default_schedules. We'll call the camera and world updaters
        ## directly in our update() and draw() methods.
        Engine.__init__(self,
            caption='03 Switch View - Press TAB to cycle views',
            resolution=(600,600),
            tile_size=(128,128), map_size=(10,10),
            frame_speed=0)  #, default_schedules=False)
        
        ## Create a second camera so we can switch between them...
        
        ## Save the main state.
        State.camera.init_position(Vec2d(State.camera.rect.size) / 2 - 5)
        State.save('main')
        State.name = 'main'
        
        ## Create a view as the alternate camera's drawing surface, then save
        ## the state under a different name.
        
        State.camera = Camera(State.camera.target,
            View(State.screen.surface, pygame.Rect(33,33,500,500)))
        State.save('small')
        
        ## Easy way to select the "next" state name.
        self.next_state = {
            'main' : 'small',
            'small' : 'main',
        }
        
        # Make some default content.
        toolkit.make_tiles()
        
        self.move_x = 0
        self.move_y = 0
        
    def update(self, dt):
        """overrides Engine.update"""
        self.update_camera_position()
        State.camera.update()

    def draw(self, interp):
        """overrides Engine.draw"""
        # Draw stuff.
## Engine does this.
##        State.camera.interpolate()
        State.camera.view.clear()
        toolkit.draw_tiles()
        if State.name == 'small':
            pygame.draw.rect(State.screen.surface, (99,99,99),
                State.camera.view.parent_rect, 1)
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
            ## Note that Camera class has a state_restored() method which is
            ## called by State.restore(). If it did not, you would see strange
            ## video behavior when swapping in a camera with stale innards. You
            ## may need to do this for your own classes if you integrate them
            ## with State.save() and State.restore().
            State.restore(self.next_state[State.name])
            State.screen.clear()
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
