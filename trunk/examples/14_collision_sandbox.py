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


__doc__ = """14_collision_sandbox.py - A sandbox / unit test for the geometry
module's collision routines in Gummworld2.

This test uses the eyeballs to validate. Do the following:
    
    1.  Ignore the lines for now.
    2.  Drag one small rect, poly, and circle completely into the other large
        2D shapes--one each. No sides should be touching
    3.  Observe that the shapes turn red as their edges cross.
    4.  Observe that the shapes stay red when one is completely inside another.
    5.  Press a key to swith between forward and reverse order collision tests.
    6.  Repeat steps 2-5 two times, rotating shape combinations.
    7.  Cross the lines and observe they turn red.
    8.  Drag a line completely into one of the 2D shapes. No sides should be
        touching.
    9.  Observe that the shapes turn red as their edges cross.
    10. Observe that the shapes stay red when one is completely inside another.
    11. Press a key to swith between forward and reverse order collision tests.
    12. Repeat steps 8-11 two times, rotating shape combinations.
"""


import pygame
from pygame.locals import *

import paths
from geometry import *


class RectGeom(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        r = self.rect
        self.tabs = [
            Rect(0,0,7,7),
        ]
        self.tabs[0].center = r.center
    collided = staticmethod(rect_collided_other)
    def update(self):
        self.rect.center = self.tabs[0].center

class LineGeom(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.tabs = [
            Rect(0,0,7,7),
            Rect(0,0,7,7),
        ]
        self.tabs[0].center = self.end_points[0]
        self.tabs[1].center = self.end_points[1]
    collided = staticmethod(line_collided_other)
    def update(self):
        self.end_points[0] = self.tabs[0].center
        self.end_points[1] = self.tabs[1].center

class PolyGeom(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.tabs = [Rect(0,0,7,7) for p in self.points]
        for i,p in enumerate(self.points):
            self.tabs[i].center = p
    collided = staticmethod(poly_collided_other)
    def update(self):
        for i,p in enumerate(self.tabs):
            self.points[i] = self.tabs[i].center

class CircleGeom(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.tabs = [
            Rect(0,0,7,7),
        ]
        self.tabs[0].center = self.origin
    collided = staticmethod(circle_collided_other)
    def update(self):
        self.origin = self.tabs[0].center


def check_collisions(sprites):
    for s in sprites:
        s.color = Color('green')
    for i,s1 in enumerate(sprites):
        for j,s2 in enumerate(sprites[i:]):
            if j > 0:
                if s1.collided(s1, s2):
                    s1.color = Color('red')
                    s2.color = Color('red')


def update_sprites(sprites):
    for s in sprites:
        s.update()


def draw_sprites(sprites):
    for s in sprites:
        if hasattr(s, 'rect'):
            draw_rect(screen, s.color, s.rect, 1)
        elif hasattr(s, 'end_points'):
            p1,p2 = s.end_points
            draw_line(screen, s.color, p1, p2, 1)
        elif hasattr(s, 'points'):
            draw_poly(screen, s.color, s.points, 1)
        elif hasattr(s, 'origin'):
            draw_circle(screen, s.color, s.origin, s.radius, 1)
        else:
            raise pygame.error, 'bad sprite %s'%str(s)
        for t in s.tabs:
            draw_rect(screen, Color('yellow'), t)


screen = pygame.display.set_mode((400,400))
pygame.display.set_caption('Sprites forward')
screen_rect = screen.get_rect()
clock = pygame.time.Clock()

rect1 = RectGeom(rect=Rect(0,0,40,40))
rect2 = RectGeom(rect=Rect(40,40,80,80))
line1 = LineGeom(end_points=[(40,170),(90,210)])
line2 = LineGeom(end_points=[(20,200),(80,250)])
poly1 = PolyGeom(points=[(202,2),(202,82),(242,42)])
poly2 = PolyGeom(points=[(202,100),(240,150),(235,200),(150,250)])
circle1 = CircleGeom(origin=(225,300), radius=20)
circle2 = CircleGeom(origin=(300,300), radius=50)

sprites_fwd = (rect1, line1, poly1, circle1, circle2, poly2, line2, rect2)
sprites_rev = list(reversed(sprites_fwd))
sprites = sprites_fwd

draw_circle = pygame.draw.circle
draw_line = pygame.draw.line
draw_rect = pygame.draw.rect
draw_poly = pygame.draw.polygon

selected = None

while 1:
    
    ## update ##
    
    clock.tick(60)
    
    for e in pygame.event.get():
        if e.type == MOUSEMOTION:
            if selected:
                selected.center = e.pos
        elif e.type == MOUSEBUTTONDOWN:
            for s in sprites:
                for t in s.tabs:
                    if t.collidepoint(e.pos):
                        selected = t
                        break
        elif e.type == MOUSEBUTTONUP:
            selected = None
        elif e.type == KEYDOWN:
            if sprites is sprites_fwd:
                sprites = sprites_rev
                pygame.display.set_caption('Sprites reversed')
            else:
                sprites = sprites_fwd
                pygame.display.set_caption('Sprites forward')
    
    check_collisions(sprites)
    update_sprites(sprites)
    
    ## draw ##
    
    screen.fill(Color('black'))
    
    draw_sprites(sprites)
    
    pygame.display.flip()
