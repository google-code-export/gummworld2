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


__doc__ = """20_context.py - Linking contexts in Gummworld2.

This demo has two contexts, a main menu and a game. Contexts are placed on a
stack. Thus, they can be stacked and then unstacked in layered fashion, or they
can pop-me-push-you as kind of a FIFO as is done in this demo.

There is no right or wrong way to use the context stack. It is as unlimited as
your imagination. Contexts can even be juggled on the stack to interesting
effect.

A context can keep its own private core objects and run like an embedded program
or it can use core objects created by another context. You can destroy them when
you're done with them, or keep them around and reenter them to resume where they
left off. The context stack and Context class work together to trigger
transition actions when a context changes state: enter, exit, pause, resume.

See the very simple context module to learn exactly how a Context behaves.

Note that Engine class is derived from Context. You should immediately think,
Aha, I don't *need* to use Engine, I can write my own Contexts. This is quite
the case.

Engine class is a Context with some magic built in. If it does not suit your
needs, you do not have to use it. Gummworld2 does not require Engine for any
reason. Engine uses the various parts of Gummworld2, not the other way around.
Engine does, however, serve as a solid recipe for how to set up and use the
core classes.

Also note that you do not have to use contexts or the context stack. They just
represent a wieldy paradigm for transitioning between loosely related modules,
e.g. splash, menus, game levels, cutscenes.
"""


import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import context, State, Engine, Vec2d, toolkit


class CameraTarget(object):
    
    def __init__(self, position=(0,0)):
        self._position = Vec2d(position)
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        self._position[:] = val


class MainMenu(Engine):
    """A menu class that just takes a keypress to continue."""
    
    def __init__(self):
        
        screen_size = Vec2d(800,600)
        
        Engine.__init__(self,
            resolution=screen_size, caption='Main Menu',
            tile_size=(128,128), map_size=(10,10),
            camera_target=CameraTarget(screen_size//2),
            frame_speed=0)
        
        font = pygame.font.SysFont(None, 22)
        self.message = font.render(
            'Press any key to continue...', True, Color('white'))
        self.message_rect = self.message.get_rect(center=self.screen.center)
        self.move = Vec2d(3,5)
        self.move_from = self.message_rect.center
    
    def update(self, dt):
        """Bounce the text around the screen."""
        sr = State.screen.rect
        mr = pygame.Rect(self.message_rect)
        mr.center += self.move
        if mr.left < 0 or mr.right >= sr.right: self.move.x *= -1
        if mr.top < 0 or mr.bottom >= sr.bottom: self.move.y *= -1
        self.move_from += self.move
    
    def draw(self, dt):
        """Draw the text with interpolated movement."""
        interp = State.clock.interpolate
        pos = toolkit.interpolated_step(self.move_from, self.move, interp)
        self.message_rect.center = round(pos.x),round(pos.y)
        State.screen.clear()
        State.screen.blit(self.message, self.message_rect)
        State.screen.flip()
    
    def on_key_down(self, unicode, key, mod):
        ## Pop the top context (which happens to be self), and push the next
        ## context. The next context automatically runs.
        context.pop()
        context.push(Game())


class Game(Engine):
    
    def __init__(self):
        
        tile_size = 128,128
        map_size = 10,10
        
        self.movex = 0
        self.movey = 0
        
        Engine.__init__(self,
            caption='Scroll Around',
            tile_size=(128,128), map_size=(10,10),
            camera_target=CameraTarget(State.screen.size//2),
            frame_speed=0)
        
        toolkit.make_tiles()
        self.visible_objects = []
    
    def update(self, dt):
        if self.movex or self.movey:
            State.camera.position += self.movex,self.movey
        State.camera.update(dt)
        self.visible_objects = toolkit.get_object_array()
    
    def draw(self, dt):
        State.screen.clear()
        toolkit.draw_object_array(self.visible_objects)
        State.screen.flip()

    def on_key_down(self, unicode, key, mod):
        if key == K_DOWN: self.movey += State.speed
        elif key == K_UP: self.movey += -State.speed
        elif key == K_RIGHT: self.movex += State.speed
        elif key == K_LEFT: self.movex += -State.speed
        elif key == K_ESCAPE: context.pop()
    
    def on_key_up(self, key, mod):
        if key == K_DOWN: self.movey -= State.speed
        elif key == K_UP: self.movey -= -State.speed
        elif key == K_RIGHT: self.movex -= State.speed
        elif key == K_LEFT: self.movex -= -State.speed
    
    def on_quit(self):
        ## Pop the top context, which is self. This exits the program because it
        ## is the last context on the stack.
        context.pop()


if __name__ == '__main__':
    menu = MainMenu()
    gummworld2.run(menu)
