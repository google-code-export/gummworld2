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


class View(object):
    """Views are used to access areas of a pygame surface. They are analogous
    to surfaces and subsurfaces.
    
    Access the pygame surface via the surface attribute.
    
    Access the surface's rect via the rect attribute.
    
    For subsurfaces, the rect for the subsurface in the parent surface can be
    accessed via the parent_rect attribute. If this instance does not represent
    a subsurface then rect and parent_rect will be equivalent.
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
        if subsurface_rect is not None:
            self.surface = surface.subsurface(subsurface_rect)
            self.parent_rect = subsurface_rect
        else:
            self.surface = surface
            self.parent_rect = self.surface.get_rect()
        self.eraser = self.surface.copy()
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
        """Clear the surface by blitting the surface in eraser attribute.
        """
        self.surface.blit(self.eraser, (0,0))
    
    def blit(self, surf, pos, area=None, special_flags=0):
        """Blit a surface to this surface.
        """
        self.surface.blit(surf, pos, area, special_flags)


class Screen(View):
    """The pygame display.
    
    Assign one of these to State.screen in order to make the library aware of
    the main display surface.
    """
    
    def __init__(self, size=0, flags=0, surface=None):
        """Initialize the pygame display.
        
        If surface is specified, it is used as the screen's surface and pygame
        display initialization is not performed.
        
        Otherwise, size and flags are used to initialize the pygame display.
        """
        if surface is None:
            surface = pygame.display.set_mode(size, flags)
        super(Screen, self).__init__(surface)
    
    def flip(self):
        """Flip the pygame display.
        """
        pygame.display.flip()


if __name__ == '__main__':
    main_screen = Screen((300,300))
    main_screen.surface.fill(pygame.Color('yellow'))
    
    mini_screen = View(main_screen.surface, (10,10,200,200))
    mini_screen.surface.fill(pygame.Color('green'))
    
    tiny_screen = View(mini_screen.surface, (10,10,100,100))
    tiny_screen.surface.fill(pygame.Color('blue'))
    
    nano_screen = View(tiny_screen.surface, (10,10,50,50))
    nano_screen.surface.fill(pygame.Color('darkblue'))
    
    last_screen = View(nano_screen.surface, (10,10,20,20))
    last_screen.surface.fill(pygame.Color('black'))
    
    main_screen.flip()
    
    while 1:
        pygame.time.wait(1000)
