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


__version__ = '0.1'
__vernum__ = (0,1)


"""view.py - Graphical view module for Gummworld2.
"""


import pygame
from pygame.locals import Color, Rect, SRCALPHA

from state import State


class Screen(object):
    
    def __init__(self, size):
        self.surface = pygame.display.set_mode(size)
        self._eraser = self.surface.copy()
        self.rect = self.surface.get_rect()
        State.canvas = Canvas()

    def clear(self):
        self.surface.blit(self._eraser, (0,0))

    def blit(self, surf, pos, rect=None):
        self.surface.blit(surf, pos, rect)

    def flip(self):
        pygame.display.flip()


class Canvas(object):
    
    def __init__(self):
        rect = pygame.display.get_surface().get_rect()
        # SRCALPHA prevents unwanted fill colors in the padded area of the
        # rotated surface.
        self.surface = pygame.surface.Surface(rect.size, SRCALPHA)
        self.eraser = pygame.surface.Surface(rect.size)
        self.eraser.fill(Color('black'))
        self.viewer = self.eraser.copy()
        pygame.draw.circle(
            self.viewer, Color('white'), rect.center, rect.width/2-2
        )
        self.viewer.set_colorkey(Color('white'))

        self.draw_viewer = False

    def clear(self):
        self.surface.blit(self.eraser, (0,0))
    
    def blit(self, sprite):
        self.surface.blit(sprite.image, sprite.rect)
    
    def draw(self):
        rotated_surface = pygame.transform.rotate(
            self.surface, State.world.avatar.rotation)
        screen = State.screen.surface
        rect = rotated_surface.get_rect()
        rect.center = screen.get_rect().center
        screen.blit(rotated_surface, rect)
        if self.draw_viewer:
            screen.blit(self.viewer, (0,0))
