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

If you want to write your own framework instead of using this one, then in
general you will still want to initialize yours in the same order as this class,
though not everything created in the constructor is required. See
Engine.__init__(), Engine.run(), and examples/00_minimum.py for helpful clues.
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

if __name__ == '__main__':
    import paths

from gummworld2 import (
    State, Screen, View, model, Map, Camera, GameClock,
    pygame_utils,
)


NO_WORLD = 0
SIMPLE_WORLD = 1
QUADTREE_WORLD = 2
PYMUNK_WORLD = 3


class Engine(object):
    
    def __init__(self,
        screen_surface=None, resolution=(600,600), display_flags=0, caption=None,
        camera_target=None, camera_view=None, camera_view_rect=None,
        tile_size=(128,128), map_size=(10,10),
        update_speed=30, frame_speed=30,
        world_type=NO_WORLD, world_args={}):
        """Construct an instance of Engine.
        
        This constructor does the following:
            
            The pygame display is initialized with an optional caption, and the
            resulting screen.Screen object is placed in State.screen.
            
            An empty map.Map object is created and placed in State.map.
            
            An empty model.World* object is created and placed in State.world.
            
            State.world_type is set to one of the engine.*_WORLD values
            corresponding to the world object in State.world.
            
            A camera.Camera object is created and placed in State.camera. The
            camera target is either taken from the camera_target argument, or an
            appropriate target for world type is created. The target is *NOT*
            added to the world, as the target does not need to be an object
            subject to game rules. If target happens to be an avatar-type object
            then add it manually to world with the rest of the world entities.
            
            A game_clock.GameClock object is created and placed in State.clock.
            
            Joystick objects are created for connected controllers.
        
        The following arguments are used to initialize a Screen object:
            
            The screen_surface argument specifies the pygame top level surface
            to use for creating the State.screen object. The presence of this
            argument overrides initialization of the pygame display, and
            resolution and display_flags arguments are ignored. Use this if
            the pygame display has already been initialized in the calling
            program.
            
            The resolution argument specifies the width and height of the
            display.
            
            The display_flags argument specifies the pygame display flags to
            pass to the display initializer.
            
            The caption argument is a string to use as the window caption.
        
        The following arguments are used to initialize a Camera object:
            
            The camera_target argument is the target that the camera will track.
            If camera_target is None, Engine will create a default target
            appropriate for the world type.
            
            The camera_view argument is a screen.View object to use as the
            camera's view.
            
            The camera_view_rect argument specifies the pygame Rect from which
            to create a screen.View object for the camera's view.
            State.screen.surface is used as the source surface. This argument is
            ignored if camera_view is not None.
        
        The following arguments are used to initialize a Map object:
            
            The tile_size and map_size arguments specify the width and height of
            a map tile, and width and height of a map in tiles, respectively.
        
        The following arguments are used to initialize a model.World* object:
            
            The world_type argument specifies which of the world classes to
            create. It must be one of engine.NO_WORLD, engine.SIMPLE_WORLD,
            engine.QUADTREE_WORLD, engine.PYMUNK_WORLD.
            
            The world_args argument is a dict that can be passed verbatim to
            the world constructor (see the World* classes in the model module)
            like so: World(**world_args).
        
        The following arguments are used to initialize a Clock object:
            
            update_speed specifies the maximum updates that can occur per
            second.
            
            frame_speed specifies the maximum frames that can occur per second.
        
        The clock sacrifices frames per second in order to achieve the desired
        updates per second. If frame_speed is 0 the frame rate is uncapped.
        """
        
        ## If you don't use this engine, then in general you will still want
        ## to initialize your State objects in the same order you see here.
        
        State.world_type = world_type
        
        if screen_surface:
            State.screen = Screen(surface=screen_surface)
        elif State.screen is None:
            if screen_surface is None:
                State.screen = Screen(resolution, display_flags)
            else:
                State.screen = Screen(surface=screen_surface)
            
        if caption is not None:
            pygame.display.set_caption(caption)
        
        State.map = Map(tile_size, map_size)
        
        ## This is the only complicated thing in here. If you want to use the
        ## camera target as a world entity, you have to use the right object
        ## type. Type checking and exception handling is purposely not done so
        ## that the code is easier to read.
        if world_type == NO_WORLD:
            State.world = model.NoWorld(State.map.rect)
            if camera_target is None:
                camera_target = model.Object()
        elif world_type == SIMPLE_WORLD:
            State.world = model.World(State.map.rect)
            if camera_target is None:
                camera_target = model.Object()
        elif world_type == PYMUNK_WORLD:
            State.world = model.WorldPymunk(State.map.rect)
            if camera_target is None:
                camera_target = model.CircleBody()
        elif world_type == QUADTREE_WORLD:
            State.world = model.WorldQuadTree(
                State.map.rect, **world_args)
            if camera_target is None:
                camera_target = model.QuadTreeObject(pygame.Rect(0,0,20,20))
        
        if camera_view is None:
            if camera_view_rect:
                camera_view = View(State.screen.surface, camera_view_rect)
            else:
                camera_view = State.screen
        State.camera = Camera(camera_target, camera_view)
        
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


if __name__ == '__main__':
    ## Multiple "apps", (aka engines, aka levels) and other settings
    from pygame.locals import *
    from gamelib import Vec2d, View, toolkit
    
    class App(Engine):
        def __init__(self, **kwargs):
            super(App, self).__init__(**kwargs)
            toolkit.make_tiles2()
            self.speed = 3
            self.movex = 0
            self.movey = 0
        def update(self):
            if self.movex or self.movey:
                State.camera.position += self.movex,self.movey
            State.camera.update()
        def draw(self):
            State.camera.interpolate()
            State.screen.surface.fill(Color('black'))
            toolkit.draw_tiles()
            if State.camera.view is not State.screen:
                pygame.draw.rect(State.screen.surface, (99,99,99),
                    State.camera.view.parent_rect, 1)
            pygame.display.flip()
        def on_key_down(self, unicode, key, mod):
            if key == K_DOWN: self.movey += self.speed
            elif key == K_UP: self.movey += -self.speed
            elif key == K_RIGHT: self.movex += self.speed
            elif key == K_LEFT: self.movex += -self.speed
            elif key == K_SPACE: State.running = False
            elif key == K_ESCAPE: quit()
        def on_key_up(self, key, mod):
            if key == K_DOWN: self.movey -= self.speed
            elif key == K_UP: self.movey -= -self.speed
            elif key == K_RIGHT: self.movex -= self.speed
            elif key == K_LEFT: self.movex -= -self.speed
    
    def make_app(num, **kwargs):
        name = 'app' + str(num)
        if name in state.states:
            State.restore(name)
            pygame.display.set_caption(State.caption+' (restored)')
        else:
            State.app = App(**kwargs)
            if num % 2:
                toolkit.make_tiles()
            else:
                toolkit.make_tiles2()
            State.camera.position = State.camera.screen_center
            State.caption = kwargs['caption']
            State.save(name)
    
    def make_app1():
        screen = pygame.display.set_mode(resolution)
        make_app(1,
            screen_surface=screen,
            tile_size=tile_size, map_size=map_size,
            caption='1:Screen')
    
    def make_app2():
        tile_size = Vec2d(32,32)
        view = View(State.screen.surface, Rect(16,16,*(tile_size*6)) )
        make_app(3,
            tile_size=tile_size, map_size=map_size,
            camera_view=view, caption='3:View+Tilesize')
    
    def make_app3():
        make_app(4,
            tile_size=tile_size, map_size=map_size,
            camera_view_rect=Rect(16,16,*(tile_size*3)),
            caption='4:Viewrect')
    
    tile_size = Vec2d(64,64)
    map_size = Vec2d(10,10)
    resolution = tile_size * 4
    
    State.default_attrs.extend(('app','caption'))
    app_num = 0
    
    while 1:
        app_num += 1
        if app_num > 3:
            app_num = 1
        if app_num == 1:   make_app1()
        elif app_num == 2: make_app2()
        elif app_num == 3: make_app3()
        elif app_num == 4: make_app4()
        State.app.run()
