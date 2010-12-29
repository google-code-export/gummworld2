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


"""engine.py - A sample engine for Gummworld2.
"""


import pygame
from pygame.locals import (
    QUIT,
    ACTIVEEVENT,
    KEYDOWN,
    KEYUP,
    MOUSEMOTION,
    MOUSEBUTTONUP,
    MOUSEBUTTONDOWN,
    JOYAXISMOTION,
    JOYBALLMOTION,
    JOYHATMOTION,
    JOYBUTTONUP,
    JOYBUTTONDOWN,
    VIDEORESIZE,
    VIDEOEXPOSE,
    USEREVENT,
)

from gamelib import (
    State, view, model, Map, Camera, Graphics, GameClock,
)


class Engine(object):

    """Subclass this class and override update() and draw(). Also override the
    on_* event handlers if you want to get a particular event type.
    """

    def __init__(self, resolution=(600,600), display_flags=0,
        tile_size=(128,128), map_size=(10,10),
        update_speed=30, frame_speed=30):
        
        ## If you don't use this engine, then in general you will still
        ## want to initialize yours in the same order you see here.
        
        State.screen = view.Screen(resolution, display_flags)
        
        State.map = Map(tile_size, map_size)
        State.world = model.World(State.map.rect)
        
        State.camera = Camera(State.avatar, State.screen.surface)
            
        State.graphics = Graphics()
        State.clock = GameClock(update_speed, frame_speed)
        
        self._get_pygame_events = pygame.event.get
        
    def run(self):
        State.running = True
        while State.running:
            if State.clock.update_ready():
                self._get_events()
                self.update()
                State.world.step()
            if State.clock.frame_ready():
                self.draw()
        
    def update(self):
        """Override this method. Called by run() when the clock signals an
        update cycle is ready.
        
        Suggestion:
            State.camera.update()
            ... custom update the rest of the game ...
        
        As an alternative to using Camera.update() you can modify the
        Camera.target.position in Engine.update(), and then call
        Camera.interpolate in Engine.draw(). In this case you will also want to
        initialize the frame speed to unlimited (0).
        """
        State.camera.update()
        
    def draw(self):
        """Override this method. Called by run() when the clock signals a
        frame cycle is ready.
        
        Suggestion:
            State.screen.clear()
            ... custom draw the screen ...
            State.screen.flip()
        """
        pass
        
    def _get_events(self):
        """Called automatically by run() each time the clock indicates an
        update cycle is ready.
        """
        for e in self._get_pygame_events():
            typ = e.type
            if typ == KEYDOWN:
                self.on_key_down(e.unicode, e.key, e.mod)
            elif typ == KEYUP:
                self.on_key_up(e.key, e.mod)
            elif typ == MOUSEMOTION:
                self.on_mouse_motion(e.pos, e.rel, e.buttons)
            elif typ == MOUSEBUTTONUP:
                self.on_mouse_button_up(e.pos, e.button)
            elif typ == MOUSEBUTTONDOWN:
                self.on_mouse_button_down(e.pos, e.button)
            elif typ == JOYAXISMOTION:
                self.on_joy_axis_motion(e.joy, e.axis, e.value)
            elif typ == JOYBALLMOTION:
                self.on_joy_ball_motion(e.joy, e.ball, e.rel)
            elif typ == JOYHATMOTION:
                self.on_joy_hat_motion(e.joy, e.hat, e.value)
            elif typ == JOYBUTTONUP:
                self.on_joy_button_up(e.joy, e.button)
            elif typ == JOYBUTTONDOWN:
                self.on_joy_button_down(e.joy, e.button)
            elif typ == VIDEORESIZE:
                self.on_video_resize(e.size, e.w, e.h)
            elif typ == VIDEOEXPOSE:
                self.on_video_expose()
            elif typ == USEREVENT:
                    self.on_user_event(e)
            elif typ == QUIT:
                    self.on_quit()
            elif typ == ACTIVEEVENT:
                self.on_active_event(e.gain, e.state)
        
    ## Override these as desired to get specific event types.
    def on_key_down(self, unicode, key, mod): pass
    def on_key_up(self, key, mod): pass
    def on_mouse_motion(self, pos, rel, buttons): pass
    def on_mouse_button_up(self, pos, button): pass
    def on_mouse_button_down(self, pos, button): pass
    def on_joy_axis_motion(self, joy, axis, value): pass
    def on_joy_ball_motion(self, joy, ball, rel): pass
    def on_joy_hat_motion(self, joy, hat, value): pass
    def on_joy_button_up(self, joy, button): pass
    def on_joy_button_down(self, joy, button): pass
    def on_video_resize(self, size, w, h): pass
    def on_video_expose(self): pass
    def on_user_event(self, e): pass
    def on_quit(self): pass
    def on_active_event(self, gain, state): pass
