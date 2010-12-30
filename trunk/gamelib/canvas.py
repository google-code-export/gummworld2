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


__doc__ = """
canvas.py - A canvas for intermediate drawing and rotation.
"""


import pygame
from pygame.locals import Color, Rect, SRCALPHA


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
        """Clear the canvas's surface.
        """
        self.surface.blit(self.eraser, (0,0))
    
    def blit(self, sprite):
        """Blit a sprite to the canvas's surface.
        """
        self.surface.blit(sprite.image, sprite.rect)
    
    def rotate(self, angle):
        """Rotate the canvas by angle.
        """
        rotated_surface = pygame.transform.rotate(
            self.surface, angle)
        screen = State.screen.surface
        rect = rotated_surface.get_rect()
        rect.center = screen.get_rect().center
        screen.blit(rotated_surface, rect)
        
    def draw(self):
        """Draw the canvas on the display.
        """
        screen.blit(self.viewer, (0,0))
