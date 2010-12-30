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


__version__ = '0.3'
__vernum__ = (0,3)


__doc__ = """screen.py - Yer basic display class for Gummworld2.
"""


import pygame

from gamelib import State, Vec2d


class Screen(object):
    
    def __init__(self, size, flags=0):
        self.surface = pygame.display.set_mode(size, flags)
        self._eraser = self.surface.copy()
        self.rect = self.surface.get_rect()
    
    @property
    def size(self): return Vec2d(self.width, self.height)
    @property
    def width(self): return self.rect.width
    @property
    def height(self): return self.rect.height
    
    def clear(self):
        self.surface.blit(self._eraser, (0,0))
    
    def blit(self, surf, pos, rect=None):
        self.surface.blit(surf, pos, rect)
    
    def flip(self):
        pygame.display.flip()
