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


"""model.py - Physics model for Gummworld2.

Everything in this module is expressed in terms of pymunk space.
"""

import pygame
import pymunk

from gamelib import State


class World(object):
    
    def __init__(self, rect, avatar=None):
        """left, bottom, right, top are bounding box edges in pymunk space"""
        self.space = pymunk.Space()
        
        self.rect = pygame.Rect(rect)
        self.bounding_box = pymunk.BB(rect.left, rect.bottom, rect.right, rect.top)
        
        if avatar is None:
            self.avatar = Avatar()
            State.avatar = self.avatar
        else:
            self.avatar = State.avatar
        self.add(self.avatar.body, self.avatar.shape)

    def add(self, *objects):
        for o in objects:
            self.space.add(o)

    def step(self):
        dt = State.clock.tick()
        self.space.step(dt)


class BasicObject(object):
    
    def __init__(self, position=(0.0,0.0), rotation=0.0, speed=1.0, *args):
        self._rotation = 0.0
        self._speed = 1.0
        self.rotation = rotation
        self.speed = speed
        self._body = None
        self._shape = None
        self._subclass_init(position, *args)

    def _subclass_init(self, *args):
        """convenient method for subclass to override for its own initialization
        
        At minimum the subclass should create a _shape and _body, or provide
        methods to do so.
        """
        pass

    @property
    def body(self):
        return self._body

    @property
    def shape(self):
        return self._shape

    @property
    def x(self):
        return self.position.x
    @x.setter
    def x(self, val):
        self.position.x = float(val)

    @property
    def y(self):
        return self.position.y
    @y.setter
    def y(self, val):
        self.position.y = float(val)

    @property
    def position(self):
        return self._body.position
    @position.setter
    def position(self, val):
        x,y = val
        self._body.position = float(x),float(y)

    @property
    def rotation(self):
        return self._rotation
    @rotation.setter
    def rotation(self, val):
        self._rotation = float(val)

    @property
    def speed(self):
        return self._speed
    @speed.setter
    def speed(self, val):
        self._speed = float(val)


class Avatar(BasicObject):
    
    def _subclass_init(self, position, *args):
        mass = 1.0
        self.radius = 14
        inertia = pymunk.moment_for_circle(mass, 0, self.radius, (0,0))
        self._body = pymunk.Body(mass, inertia)
        self.body.position = position
        self._shape = pymunk.Circle(self.body, self.radius)
