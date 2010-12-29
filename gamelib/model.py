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
            self.avatar = CircleBody()
            State.avatar = self.avatar
        else:
            self.avatar = State.avatar
        if avatar not in self.space.bodies:
            self.add(self.avatar, self.avatar.shape)

    def add(self, *objects):
        for o in objects:
            self.space.add(o)

    def step(self):
        self.space.step(State.dt)


class CircleBody(pymunk.Body):
    
    def __init__(self, mass=1.0, radius=1.0,
        position=(0.0,0.0), angle=0.0, velocity=(0,0)):

        inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))
        super(CircleBody, self).__init__(mass, inertia)
        self.shape = pymunk.Circle(self, radius)

        self.position = position
        self.angle = angle
        self.velocity = velocity
