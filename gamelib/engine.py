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


__doc__ = """
engine.py - A sample engine for Gummworld2.

This module provides an Engine class that can be subclassed for an application
framework that's easy to use.

The run loop keeps time via the game clock. update() and event handlers are
called every time an update cycle is ready. draw() is called every time a frame
cycle is ready.

The subclass should override update() and draw() for its own purposes. If the
subclass wants to get events for a particular type, all it needs to do is
override the event handler for that type.

If you want to write your own engine instead of using this one, then in general
you will still want to initialize yours in the same order as this class. See
__init__() and run() for the details.
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
try:
    import pymunk
except:
    pymunk = None

from gamelib import (
    State, Screen, model, Map, Camera, Graphics, GameClock,
    pygame_utils,
)


NO_WORLD = 0
SIMPLE_WORLD = 1
QUADTREE_WORLD = 2
PYMUNK_WORLD = 3


class Engine(object):
    
    def __init__(self, camera_target=None,
        resolution=(600,600), display_flags=0, caption=None,
        tile_size=(128,128), map_size=(10,10),
        update_speed=30, frame_speed=30,
        world_type=NO_WORLD,
        **kwargs):
        """Construct an instance of Engine.
        
        The camera_target argument is the target that the camera will track. If
        camera_target is None Engine will create a default target depending on
        whether pymunk is used (see following notes).
        
        The resolution argument specifies the width and height of the display.
        
        The display_flags argument specifies the pygame display flags to pass
        to the display initializer.
        
        The caption argument is a string to use as the window caption.
        
        The tile_size and map_size arguments specify the width and height of
        a map tile, and width and height of a map in tiles, respectively.
        
        The update_speed and frame_speed arguments control the game clock.
        update_speed specifies the maximum updates that can occur per second.
        frame_speed specifies the maximum frames that can occur per second. The
        clock sacrifices frames per second in order to achieve the desired
        updates per second. If frame_speed is 0 the frame rate is uncapped.
        
        The use_pymunk argument specifies whether to use pymunk for the model
        (world and camera.target). If use_pymunk is True and a camera_target is
        specified, the camera_target must be similarly constructed to a
        model.CircleBody object. Which is to say it must be an instance of
        pymunk.Body, and have a shape attribute that is an instance of
        pymunk.Shape. If use_pymunk is False then camera_target can be any class
        that has a position attribute that is an instance of Vec2d.
        """
        
        ## If you don't use this engine, then in general you will still
        ## want to initialize yours in the same order you see here.
        
        State.world_type = world_type
        
        State.screen = Screen(resolution, display_flags)
        if caption is not None:
            pygame.display.set_caption(caption)
        
        State.map = Map(tile_size, map_size)
        
        ## This is the only convoluted thing in here. If you want to use pymunk
        ## you have to use the right object type for a camera target. Type
        ## checking and exception handling is purposely not done so that the
        ## code is easier to read. If it blows up you should be able to figure
        ## it out from the default stack trace.
        if world_type == NO_WORLD:
            State.world = model.NoWorld(State.map.rect)
            if camera_target is None:
                camera_target = model.Object()
        elif world_type == SIMPLE_WORLD:
            State.world = model.World(State.map.rect)
            if camera_target is None:
                camera_target = model.Object()
            State.world.add(camera_target)
        elif world_type == PYMUNK_WORLD:
            State.world = model.WorldPymunk(State.map.rect)
            if camera_target is None:
                camera_target = model.CircleBody()
            State.world.add(camera_target, camera_target.shape)
        elif world_type == QUADTREE_WORLD:
            qt_min_size = kwargs.get('quadtree_min_size', (128,128))
            qt_worst_case = kwargs.get('quadtree_worst_case', 0)
            State.world = model.WorldQuadTree(
                State.map.rect, qt_min_size, qt_worst_case)
            if camera_target is None:
                qt_position = kwargs.get('quadtree_object_position', (0,0))
                qt_rect = kwargs.get(
                    'quadtree_object_rect', pygame.Rect(0,0,20,20))
                camera_target = model.QuadTreeObject(qt_rect, qt_position)
        
        State.camera = Camera(camera_target, State.screen.surface)
        
        State.graphics = Graphics()
        State.clock = GameClock(update_speed, frame_speed)
        
        self._joysticks = pygame_utils.init_joystick()
        self._get_pygame_events = pygame.event.get
        
    def run(self):
        """Start the run loop.
        
        To exit the run loop gracefully, set State.running=False.
        """
        State.running = True
        while State.running:
            State.dt = State.clock.tick()
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
            move_camera()
            State.camera.update()
            ... custom update the rest of the game ...
        """
        pass
        
    def draw(self):
        """Override this method. Called by run() when the clock signals a
        frame cycle is ready.
        
        Suggestion:
            State.screen.clear()
            State.camera.interpolate()
            ... custom draw the screen ...
            State.screen.flip()
        """
        pass
        
    @property
    def joysticks(self):
        """List of initialized joysticks.
        """
        return list(self._joysticks)
    
    def _get_events(self):
        """Get events and call the handler. Called automatically by run() each
        time the clock indicates an update cycle is ready.
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
        
    ## Override an event handler to get specific events.
    def on_active_event(self, gain, state): pass
    def on_joy_axis_motion(self, joy, axis, value): pass
    def on_joy_ball_motion(self, joy, ball, rel): pass
    def on_joy_button_down(self, joy, button): pass
    def on_joy_button_up(self, joy, button): pass
    def on_joy_hat_motion(self, joy, hat, value): pass
    def on_key_down(self, unicode, key, mod): pass
    def on_key_up(self, key, mod): pass
    def on_mouse_button_down(self, pos, button): pass
    def on_mouse_button_up(self, pos, button): pass
    def on_mouse_motion(self, pos, rel, buttons): pass
    def on_quit(self): pass
    def on_user_event(self, e): pass
    def on_video_expose(self): pass
    def on_video_resize(self, size, w, h): pass
