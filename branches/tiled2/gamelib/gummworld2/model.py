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


__doc__ = """model.py - Physics model for Gummworld2.

If pymunk is installed and can be imported, then the pymunk subclasses
WorldPymunk and various bodies will be created. Otherwise, only the classes
World and Object will be available.
"""

import pygame
try:
    import pymunk
except:
    pymunk = None

from gummworld2.geometry import RectGeometry, CircleGeometry, PolyGeometry
from gummworld2 import State, Vec2d, data


class NoWorld(object):
    
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
    
    def add(self, *args):
        pass
    
    def step(self, dt):
        pass


class Object(object):
    """An object model suitable for use as a Camera target or an autonomous
    object in World.
    
    Similar to pygame.sprite.Sprite, without the graphics and rect. Subclass
    this and extend.
    """
    
    def __init__(self, position=(0,0)):
        self._position = Vec2d(position)
        self._worlds = {}
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        p = self._position
        p.x,p.y = val
    
    def update(self, *args):
        pass
    
    def worlds(self):
        return self._worlds.keys()
    
    def kill(self):
        for w in self._worlds:
            w.remove(self)
        self._worlds.clear()


class World(object):
    """A container for model.Objects.
    
    Similar to pygame.sprite.AbstractGroup. Not compatible with
    pygame.sprite.Sprite.
    
    If you want the world to store pygame sprites, substitute a group and that
    has a rect attribute and step() method.
    """
    
    def __init__(self, rect):
        """rect is bounding box edges in pygame space"""
        self.rect = pygame.Rect(rect)
        self._object_dict = {}
    
    def add(self, *objs):
        """Add objects to the world."""
        for o in objs:
            self._object_dict[o] = 1
            if not hasattr(o, '_worlds'):
                o._worlds = {}
            o._worlds[self] = 1
    
    def remove(self, *objs):
        for o in objs:
            if o in self._object_dict:
                del self._object_dict[o]
            if hasattr(o, '_worlds') and self in o._worlds:
                del o._worlds[self]
    
    def objects(self):
        return self._object_dict.keys()
    
    def step(self, dt):
        for o in self.objects():
            o.update()
    
    def __iter__(self):
        return iter(self.objects())
    
    def __contains__(self, obj):
        return obj in self._object_dict
    
    def __nonzero__(self):
        return (len(self._object_dict) != 0)
    
    def __len__(self):
        """len(group)
           number of sprites in group
    
           Returns the number of sprites contained in the group."""
        return len(self._object_dict)
    
    def __repr__(self):
        return "<%s(%d objects)>" % (self.__class__.__name__, len(self))


if pymunk is not None:
    
    class WorldPymunk(pymunk.Space):
        """If pymunk is available use WorldPymunk. This WorldPymunk class sets up
        the pymunk space, and abstracts the step() method.
        """
        
        def __init__(self, rect):
            """left, bottom, right, top are bounding box edges in pygame space"""
            super(WorldPymunk, self).__init__()
            self.rect = pygame.Rect(rect)
        
        def step(self, dt):
            super(WorldPymunk, self).step(dt)


    class CircleBody(pymunk.Body):
        """A pymunk.Circle with defaults for position, angle, velocity, radius,
        mass, and the shape.
        """
        
        def __init__(self, mass=1.0, radius=1.0,
            position=(0.0,0.0), angle=0.0, velocity=(0,0)):

            inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))
            super(CircleBody, self).__init__(mass, inertia)
            self.shape = pymunk.Circle(self, radius)

            self.position = position
            self.angle = angle
            self.velocity = velocity
