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


"""11_multiple_maps_and_cameras.py - An example of two scrolling maps and
cameras in Gummworld2.

This demo leverages State.save() and State.restore() to manage simultaneously
scrolling maps.
"""


import pygame
from pygame.locals import Rect, K_ESCAPE, K_TAB, K_UP, K_DOWN, K_LEFT, K_RIGHT

import paths
from gamelib import *
from gamelib import state


class App(Engine):
    
    def __init__(self):
        self.caption = '11 Multiple Maps and Cameras'
        
        resolution = Vec2d(600,600)
        half_width = resolution.x // 2
        full_height = resolution.y
        
        super(App, self).__init__(
            resolution=resolution, caption=self.caption,
            camera_view_rect=Rect(0,0, half_width,full_height),
            frame_speed=0)
        
        ## The two views will each have their own camera and map.
        State.default_attrs = ['camera','map']
        
        ## Set up the first view. Save the state.
        State.camera.position = State.world.rect.center
        toolkit.make_tiles()
        self.view1 = State.camera.view
        State.save(self.view1)
        
        ## Set up the second view. We can get tile_size and map_size from the
        ## first map. Save the state.
        self.view2 = View(State.screen.surface,
            Rect(half_width,0, half_width,full_height))
        State.camera = Camera(model.Object(), self.view2)
        State.camera.position = State.world.rect.center
        State.map = Map(State.map.tile_size, State.map.map_size)
        toolkit.make_tiles2()
        State.save(self.view2)
        
        # Add some data to contribute to motion.
        self.view1.angle = 180
        self.view1.step = -6
        self.view1.radius = 64
        self.view2.angle = 0
        self.view2.step = -3
        self.view2.radius = 64
        
    def update(self):
        """overrides Engine.update"""
        ## Restore each view and update its camera.
        for view in (self.view1, self.view2):
            State.restore(view)
            self.update_camera_position(view)
            State.camera.update()
        if view.angle == 0:
            pygame.display.set_caption(
                self.caption + ' - %d fps' % State.clock.get_fps())

    def update_camera_position(self, view):
        """move the camera's position
        """
        angle = view.angle
        step = view.step
        angle = (angle + step) % 360
        radius = view.radius
        origin = State.world.rect.center
        State.camera.position = geometry.point_on_circumference(
            origin, radius, angle)
        view.angle = angle
    
    def draw(self):
        """overrides Engine.draw"""
        ## Restore each view and draw its map.
        for view in (self.view1, self.view2):
            State.restore(view)
            State.camera.interpolate()
            view.clear()
            toolkit.draw_tiles()
        State.screen.flip()
        
    def on_key_down(self, unicode, key, mod):
        if key == K_ESCAPE:
            quit()
    
    def on_quit(self):
        quit()


if __name__ == '__main__':
    app = App()
    app.run()
