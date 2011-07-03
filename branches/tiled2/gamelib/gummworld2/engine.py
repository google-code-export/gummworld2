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


__doc__ = """engine.py - A sample engine for Gummworld2.

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


import sys

import pygame
from pygame.locals import (
    QUIT,
    KEYDOWN, KEYUP,
    MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN,
    JOYAXISMOTION, JOYBALLMOTION, JOYHATMOTION, JOYBUTTONUP, JOYBUTTONDOWN,
    ACTIVEEVENT, VIDEORESIZE, VIDEOEXPOSE,
    USEREVENT,
)
try:
    import pymunk
except:
    pymunk = None

if __name__ == '__main__':
    import paths

from gummworld2 import (
    State, Context, Screen, View, Map, Camera, GameClock,
    context, model, pygame_utils,
)


NO_WORLD = 0
SIMPLE_WORLD = 1
QUADTREE_WORLD = 2
PYMUNK_WORLD = 3


class Engine(Context):
    
    NO_WORLD = NO_WORLD
    SIMPLE_WORLD = SIMPLE_WORLD
    QUADTREE_WORLD = QUADTREE_WORLD
    PYMUNK_WORLD = PYMUNK_WORLD
    
    def __init__(self,
        screen_surface=None, resolution=None, display_flags=0, caption=None,
        camera_target=None, camera_view=None, camera_view_rect=None,
        map=None, tile_size=None, map_size=None,
        update_speed=30, frame_speed=30, default_schedules=True,
        world_type=NO_WORLD, world_args={},
        set_state=True):
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
        
        Engine.update() and Engine.draw() are registered as callbacks in the
        clock.
        
        By default the Engine class schedules these additional items:
            
            clock.schedule_update_priority(self._get_event, -2.0)
            clock.schedule_update_priority(State.world.step, -1.0)
            clock.schedule_update_priority(State.camera.update, 1.0)
            clock.schedule_frame_priority(State.camera.interpolate, -1.0)
            
        The first three items coincide with the clock's callback to
        Engine.update(). The last item coincides with Engine.draw().
        
        The use of priorities allows user items to be scheduled in between these
        default items by using an appropriate float value: lower priorities will
        be run first. See gameclock.GameClock.schedule_*_priority().
        
        To prevent scheduling the world and camera items, pass the constructor
        argument default_schedules=False. If these are not scheduled by Engine,
        the using program will either need to schedule them or place them
        directly in the overridden update() and draw() methods, as appropriate.
        """
        
        if __debug__: print 'Engine: -- new engine --'
        
        Context.__init__(self)
        
        ## If you don't use this engine, then in general you will still want
        ## to initialize your State objects in the same order you see here.
        
        self.world_type = world_type
        self.screen = None
        self.caption = caption
        self.map = None
        self.world = None
        self.camera = None
        self.camera_target = camera_target
        self.clock = None
        
        ## Screen.
        if screen_surface:
            if __debug__: print 'Engine: Screen(surface=screen_surface)'
            self.screen = Screen(surface=screen_surface)
        elif resolution:
            if __debug__: print 'Engine: Screen(resolution, display_flags)'
            self.screen = Screen(resolution, display_flags)
        else:
            if __debug__: print 'Engine: SKIPPING screen creation: no screen surface or resolution'
            self.screen = State.screen
        
        ## Map.
        if map:
            if __debug__: print 'Engine: using pre-made map'
            self.map = map
        elif tile_size and map_size:
            if __debug__: print 'Engine: Map(tile_size, map_size)'
            self.map = Map(tile_size, map_size)
        else:
            if __debug__: print 'Engine: SKIPPING map creation: no map, tile_size, or map_size'
        
        ## If you want to use the camera target as a world entity, you have to
        ## use the right object type. Type checking and exception handling are
        ## not done. This is to allow flexible initialization of the Engine
        ## context.
        if __debug__ and self.camera_target:
            print 'Engine: using pre-made camera target'
        if not self.map:
            if __debug__: print 'Engine: SKIPPING world creation: no map'
            pass
        elif world_type == NO_WORLD:
            if __debug__: print 'Engine: NoWorld(self.map.rect)'
            self.world = model.NoWorld(self.map.rect)
            if camera_target is None:
                if __debug__: print 'Engine: making camera target Object()'
                self.camera_target = model.Object()
        elif world_type == SIMPLE_WORLD:
            if __debug__: print 'Engine: World(self.map.rect)'
            self.world = model.World(self.map.rect)
            if camera_target is None:
                if __debug__: print 'Engine: making camera target Object()'
                self.camera_target = model.Object()
        elif world_type == PYMUNK_WORLD:
            if __debug__: print 'Engine: WorldPymunk(self.map.rect)'
            self.world = model.WorldPymunk(self.map.rect)
            if camera_target is None:
                if __debug__: print 'Engine: making camera target CircleBody()'
                self.camera_target = model.CircleBody()
        elif world_type == QUADTREE_WORLD:
            if __debug__: print 'Engine: WorldQuadTree(self.map.rect, **world_args)'
            self.world = model.WorldQuadTree(self.map.rect, **world_args)
            if camera_target is None:
                if __debug__: print 'Engine: making camera target QuadTreeObject()'
                self.camera_target = model.QuadTreeObject(pygame.Rect(0,0,20,20))
        
        ## Create the camera.
        if any((self.camera_target, camera_view, camera_view_rect)):
            if camera_view:
                if __debug__: print 'Engine: using pre-made camera view'
            else:
                if camera_view_rect:
                    if __debug__: print 'Engine: making camera view from rect'
                    camera_view = View((self.screen or State.screen).surface, camera_view_rect)
                else:
                    if __debug__: print 'Engine: making camera view from screen'
                    camera_view = self.screen
            if __debug__: print 'Engine: making camera'
            self.camera = Camera(self.camera_target, camera_view)
        else:
            if __debug__: print 'Engine: SKIPPING camera creation: no camera target, view, or view rect'
        
        ## Clock setup. Use pygame.time.get_ticks unless in Windows.
        if sys.platform in('win32','cygwin'):
            if __debug__: print 'Engine: using time.clock for Windows platform'
            time_source = None
        else:
            if __debug__: print 'Engine: using pygame.time.get_ticks for non-Windows platform'
            time_source = lambda:pygame.time.get_ticks()/1000.
        ## Create the clock, specifying callbacks for update() and draw().
        if __debug__: print 'Engine: creating GameClock'
        self.clock = GameClock(
            update_speed, frame_speed,
            update_callback=self.update, frame_callback=self.draw,
            time_source=time_source)
        
        ## Default schedules.
        if __debug__: print 'Engine: scheduling _get_events at priority -2.0'
        self.clock.schedule_update_priority(self._get_events, -2.0)
        if default_schedules:
            if __debug__: print 'Engine: scheduling default items'
            self.schedule_default()
        
        ## Init joysticks.
        if not pygame.joystick.get_init():
            if __debug__: print 'Engine: initializing joysticks'
            self._joysticks = pygame_utils.init_joystick()
        self._get_pygame_events = pygame.event.get
        
        ## Initialize State.
        if set_state:
            if __debug__: print 'Engine: copying my objects to State'
            self.set_state()
    
    def enter(self):
        """Called when the context is entered.
        
        If you override this, make sure you call the super.
        """
        self.set_state()
    
    def resume(self):
        """Called when the context is resumed.
        
        If you override this, make sure you call the super.
        """
        self.set_state()
    
    def set_state(self):
        if self.world_type is not None:
            State.world_type = self.world_type
        if self.screen is not None:
            State.screen = self.screen
        if self.caption is not None:
            pygame.display.set_caption(self.caption)
        if self.map is not None:
            State.map = self.map
        if self.world is not None:
            State.world = self.world
        if self.camera is not None:
            State.camera = self.camera
        if self.camera_target is not None:
            State.camera_target = self.camera_target
        if self.clock is not None:
            State.clock = self.clock
    
    def schedule_default(self):
        """Schedule default items.
        
        Note: These are not tracked. If you intend to manually replace
        State.world or State.camera after constructing the Engine object,
        you'll likely want to unschedule some or all of these and manage the
        schedules yourself. If you replace the objects without unscheduling
        their callbacks, the lost references will result in memory and CPU
        leaks.
        """
        if self.world and isinstance(self.world, model.WorldPymunk):
            self.clock.schedule_update_priority(self.world.step, -1.0)
        if self.camera:
            self.clock.schedule_update_priority(self.camera.update, 1.0)
            self.clock.schedule_frame_priority(self.camera.interpolate, -1.0)
    
    def unschedule_default(self):
        """Unschedule default items.
        """
        if self.world:
            self.clock.unschedule(self.world.step)
        if self.camera:
            self.clock.unschedule(self.camera.update)
            self.clock.unschedule(self.camera.interpolate)
    
    def update(self, dt):
        """Override this method. Called by run() when the clock signals an
        update cycle is ready.
        
        Suggestion:
            move_camera()
            State.camera.update()
            ... custom update the rest of the game ...
        """
        pass
    
    def draw(self, dt):
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
    
    def _get_events(self, dt):
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


def run(app):
    """Push app onto the context stack and start the run loop.
    
    To exit the run loop gracefully, call context.pop().
    """
    context.push(app)
    while context.top():
        State.clock.tick()


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
