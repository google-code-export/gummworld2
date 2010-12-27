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


"""__init__.py - Geometry module for Gummworld2.
"""


from math import cos, sin, radians

import pygame


class Ellipse(object):
    
    def __init__(self, origin, radius_x, radius_y):
        """Ellipse(origin, radius_x, radius_y) -> Ellipse
        
        origin -> sequence of int or float; origin (x,y)
        radius_x -> int or float; radius along x-axis
        radius_y -> int or float; radius along y-axis
        """
        self.origin = origin
        self.radius_x = radius_x
        self.radius_y = radius_y
        
    def draw(self, surface, color, arcs=360):
        """Ellipse.draw(surface, color, arcs=360) : None
        
        Draw an ellipse on a pygame surface in the specified color.
        
        surface -> pygame surface
        color -> pygame color
        arcs -> number of slices in the circumference; normally 360 or 720 will
            suffice
        """
        pygame.draw.lines(surface, color, True,
            [(int(round(x)),int(round(y))) for x,y in self.plot(arcs)])
        
    def plot(self, arcs=360):
        """Ellipse.plot(arcs) : list
        
        Plot the circumference of an ellipse and return the points in a list.
        
        arcs -> number of slices in the circumference; normally 360 or 720 will
            suffice
        
        The list that is returned is a sequence of (x,y) tuples suitable for
        use with pygame.draw.lines().
        """
        circumference = []
        arcs = int(round(arcs))
        for n in xrange(0, arcs):
            angle = 360.0 * n / arcs
            x,y = self.point(angle)
            circumference.append((x,y))
        return circumference
        
    def point(self, angle):
        """Ellipse.point(angle) : (x,y)
        
        Plot a point on the circumference of an ellipse at the specified angle.
        The point is returned as an (x,y) tuple.
        
        angle -> the angle in degrees
        """
        rad = radians(angle)
        x = self.radius_x * cos(rad)
        y = self.radius_y * sin(rad)
        ox,oy = self.origin
        return x+ox,y+oy
