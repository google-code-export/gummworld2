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


__doc__ = """screen.py - Yer basic display class for Gummworld2.
"""


import pygame

if __name__ == '__main__':
    import paths

from gamelib import State, Vec2d


class Surface(object):
    """Convenience class for creating and using subsurfaces.
    
    The surface can be accessed via the surface attribute.
    
    The surface's rect can be accessed via the rect attribute.
    
    For subsurfaces the parent rect that was used to create the subsurface can
    be access via the super_rect attribute. If this instance does not represent
    a subsurface then rect and super_rect will be equivalent.
    """
    
    def __init__(self, surface, subsurface_rect=None):
        """Create an instance of Surface.
        
        If only surface is specified then it is used as the instance's surface.
        If subsurface_rect is specified then a subsurface of the surface
        argument is gotten for the instance's surface.
        
        The surface argument is a pygame surface.
        
        The subsurface_rect argument is the area of a subsurface to get from
        the surface argument.
        """
        if subsurface_rect:
            self.surface = surface.subsurface(subsurface_rect)
            self.super_rect = subsurface_rect
        else:
            self.surface = surface
            self.super_rect = self.surface.get_rect()
        self._eraser = self.surface.copy()
        self.rect = self.surface.get_rect()
    
    @property
    def size(self):
        """The size of the surface.
        """
        return Vec2d(self.width, self.height)
    @property
    def width(self):
        """The width of the surface.
        """
        return self.rect.width
    @property
    def height(self):
        """The height of the surface.
        """
        return self.rect.height
    @property
    def center(self):
        """The center coordinate of the surface.
        """
        return self.rect.center
    @property
    def abs_offset(self):
        """The absolute offset of the subsurface.
        """
        return self.surface.abs_offset()

    def clear(self):
        """Clear the surface by blitting the surface in _eraser attribute.
        """
        self.surface.blit(self._eraser, (0,0))
    
    def blit(self, surf, pos, rect=None):
        """Blit a surface to this surface.
        """
        self.surface.blit(surf, pos, rect)


class Screen(Surface):
    """The pygame display.
    
    Create one of these to open a window
    """
    
    def __init__(self, size, flags=0):
        """Initialize the pygame display.
        """
        super(Screen, self).__init__(pygame.display.set_mode(size, flags))
    
    def flip(self):
        """Flip the pygame display.
        """
        pygame.display.flip()


if __name__ == '__main__':
    main_screen = Screen((300,300))
    main_screen.surface.fill(pygame.Color('yellow'))
    
    mini_screen = Surface(main_screen.surface, (10,10,200,200))
    mini_screen.surface.fill(pygame.Color('green'))
    
    tiny_screen = Surface(mini_screen.surface, (10,10,100,100))
    tiny_screen.surface.fill(pygame.Color('blue'))
    
    nano_screen = Surface(tiny_screen.surface, (10,10,50,50))
    nano_screen.surface.fill(pygame.Color('darkblue'))
    
    last_screen = Surface(nano_screen.surface, (10,10,20,20))
    last_screen.surface.fill(pygame.Color('black'))
    
    main_screen.flip()
    
    while 1:
        pygame.time.wait(1000)
