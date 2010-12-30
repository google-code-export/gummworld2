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
try:
    import pymunk
except:
    pymunk = None

from gamelib import State, Vec2d


class Avatar(object):
    """A dumb avatar model that can be used as a camera target. It has only a
    position attribute as Vec2d.
    """
    
    def __init__(self, position=(0,0)):
        self._position = Vec2d(position)
    
    @property
    def position(self): return self._position
    @position.setter
    def position(self, val):
        p = self._position
        p.x,p.y = val


class World(list):
    """If pymunk is not available, use World. This World class is minimally
    compatible with WorldPymunk class for pymunk. However, any code calling
    unsupported pymunk.Space methods will fail.
    """
    
    def __init__(self, rect):
        """rect is bounding box edges in pygame space"""
        super(World, self).__init__()
        self.rect = pygame.Rect(rect)
    
    def add(self, *objects):
        """Add objects to the world."""
        self.extend(objects)
    
    def step(self):
        """Override this method if your world is supposed to do something."""
        pass


if pymunk is not None:
    
    class WorldPymunk(pymunk.Space):
        """If pymunk is available use WorldPymunk. This WorldPymunk class sets up
        the pymunk space, and abstracts the step() method.
        """
        
        def __init__(self, rect):
            """left, bottom, right, top are bounding box edges in pygame space"""
            super(WorldPymunk, self).__init__()
            self.rect = pygame.Rect(rect)
        
        def step(self):
            super(WorldPymunk, self).step(State.dt)


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
