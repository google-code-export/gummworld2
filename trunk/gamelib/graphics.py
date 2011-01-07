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


__version__ = '0.4'
__vernum__ = (0,4)


__doc__ = """graphics.py - Graphics module for Gummworld2.

Various tools for creating graphics. This is an unfinished concept.
"""


import pygame
from pygame.locals import Color, Rect

from gamelib import State


class Graphics(object):

    _rect = Rect(0,0,0,0)
    
    def draw_bounding_box(self, surface, bb):
        rect = self._rect
        world_to_screen = State.camera.world_to_screen
        rect.topleft = world_to_screen((bb.left,bb.top))
        rect.size = world_to_screen((bb.right,bb.bottom)) - rect.topleft
        pygame.draw.rect(surface, Color('white'), rect, 1)
