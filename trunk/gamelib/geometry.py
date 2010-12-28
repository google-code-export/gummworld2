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


"""geometry.py - Geometry module for Gummworld2.
"""


from math import atan2, cos, sin, pi, radians

import pygame


class Ellipse(object):
    
    def __init__(self, origin, radius_x, radius_y):
        """Ellipse(origin, radius_x, radius_y) : Ellipse
        
        origin -> sequence of int or float; origin (x,y)
        radius_x -> int or float; radius along x-axis
        radius_y -> int or float; radius along y-axis
        """
        self.origin = origin
        self.radius_x = radius_x
        self.radius_y = radius_y
        
        self._points = None
        self._dirty = True
    
    @property
    def origin(self):
        return self._origin
    @origin.setter
    def origin(self, val):
        self._origin = val
        self._dirty = True
        
    @property
    def radius_y(self):
        return self._radius_y
    @radius_y.setter
    def radius_y(self, val):
        self._radius_y = val
        self._dirty = True
        
    @property
    def radius_x(self):
        return self._radius_x
    @radius_x.setter
    def radius_x(self, val):
        self._radius_x = val
        self._dirty = True
        
    def draw(self, surface, color, arcs=360):
        """Ellipse.draw(surface, color, arcs=360) : None
        
        Draw an ellipse on a pygame surface in the specified color.
        
        surface -> pygame surface
        color -> pygame color
        arcs -> number of slices in the circumference; normally 360 or 720 will
            suffice
        """
        if not self._dirty:
            points = self._points
        else:
            points = self.plot(arcs)
        pygame.draw.lines(surface, color, True,
            [(int(round(x)),int(round(y))) for x,y in points])
        
    def plot(self, arcs=360):
        """Ellipse.plot(arcs) : list
        
        Plot the circumference of an ellipse and return the points in a list.
        
        arcs -> number of slices in the circumference; normally 360 or 720 will
            suffice
        
        The list that is returned is a sequence of (x,y) tuples suitable for
        use with pygame.draw.lines().
        """
        if not self._dirty:
            return list(self._points)
        else:
            circumference = []
            arcs = int(round(arcs))
            for n in xrange(0, arcs):
                angle = 360.0 * n / arcs
                x,y = self.point(angle)
                circumference.append((x,y))
            self._points = circumference
            self._dirty = False
            return circumference
        
    def point(self, angle):
        """Ellipse.point(angle) : (x,y)
        
        Plot a point on the circumference of an ellipse at the specified angle.
        The point is returned as an (x,y) tuple.
        
        angle -> the angle in degrees
        """
        # angle-90 converts screen space to math function space
        rad = radians(angle-90)
        x = self.radius_x * cos(rad)
        y = self.radius_y * sin(rad)
        ox,oy = self.origin
        return x+ox,y+oy


class Diamond(pygame.Rect):
    
    def __init__(self, *args):
        """Diamond(left, top, width, height) : Rect
        Diamond((left, top), (width, height)) : Rect
        Diamond(object) : Rect
        
        Construct it like a pygame.Rect. All the Rect attributes and methods
        are available.
        
        In addition, there are read-only attributes for:
            *   Individual corners: top_center, right_center, bottom_center, and
                left_center.
            *   Individual edges: side_a, side_b, side_c, side_d.
            *   All corners as a tuple of coordinates: corners.
            *   All edges as a tuple of line segments: edges.
        """
        super(Diamond, self).__init__(*args)
    
    @property
    def top_center(self): return self.centerx,self.top
    @property
    def right_center(self): return self.right,self.centery
    @property
    def bottom_center(self): return self.centerx,self.bottom
    @property
    def left_center(self): return self.left,self.centery
    
    @property
    def side_a(self): return self.top_center,self.right_center
    @property
    def side_b(self): return self.right_center,self.bottom_center
    @property
    def side_c(self): return self.bottom_center,self.left_center
    @property
    def side_d(self): return self.left_center,self.top_center

    @property
    def corners(self):
        return self.top_center,self.right_center,self.bottom_center,self.left_center
    @property
    def edges(self):
        return self.side_a,self.side_b,self.side_c,self.side_d


def angle_of(origin, end_point):
    """angle_of(point) : float
    
    Calculate the angle between the vector defined by end points (origin,point)
    and the Y axis. All input and output values are in terms of pygame screen
    space. Returns degrees as a float.
    
    origin -> sequence; origin point (x1,y1).
    point -> sequence; end point (x2,y2).
    """
    x1,y1 = origin
    x2,y2 = end_point
    return (atan2(y2-y1, x2 - x1) * 180.0 / pi + 90.0) % 360.0


def distance(a, b):
    """distance(a, b) : int
    
    Calculate the distance between points a and b. Returns distance as a float.
    
    a -> sequence; point (x1,y1).
    b -> sequence; point (x2,y2).
    """
    x1,y1 = a
    x2,y2 = b
    diffx = x1 - x2
    diffy = y1 - y2
    return (diffx*diffx) ** 0.5 + (diffy*diffy) ** 0.5


def lines_intersection(line_1, line_2):
    """lines_intersection(line_1, line_2) : (x,y)
    
    line_1 -> sequence; the two end points of the first line.
    line_2 -> sequence; the two end points of the second line.
    
    Determines the intersection point of the line segment defined by line_1 with
    the line segment defined by line_2.
    
    Returns tuple (x,y) representing the intersection point. If no determinable
    intersection point is found, (False,False) is returned. If the lines
    coincide, in which case all points intersect, (True,True) is returned.
    
        x,y = lines_intersection(...)
        if x is True: ... lines coincide
        elif x is False: ... no intersection
        else: ... use x,y as a point
    
    This function always returns a tuple. This is intended to simplify handling
    the return data type.
    """
    a,b = (x1,y1),(x2,y2) = line_1
    c,d = (x3,y3),(x4,y4) = line_2
    
    # Fail if either line segment is zero-length.
    if a == b or c == d:
        return (False,False)

    sx1 = float(x2 - x1); sy1 = float(y2 - y1)
    sx2 = float(x4 - x3); sy2 = float(y4 - y3)

    # Fail if lines coincide (end points are along the same line).
    s1 = (-sx2 * sy1 + sx1 * sy2)
    t1 = (-sx2 * sy1 + sx1 * sy2)
    if s1 == 0 or t1 == 0:
        return (True,True)

    s = (-sy1 * (x1 - x3) + sx1 * (y1 - y3)) / s1
    t = ( sx2 * (y1 - y3) - sy2 * (x1 - x3)) / t1

    if s >= 0 and s <= 1 and t >= 0 and t <= 1:
        # Collision detected
        i_x = x1 + (t * sx1)
        i_y = y1 + (t * sy1)
        return (i_x,i_y)

    # No collision
    return (False,False)


def point_on_circumference(center, radius, degrees_):
    """point_on_circumference(center, radius, degrees_) : (x,y)
    
    center -> tuple; (x,y) origin of the circle.
    radius -> number; length of the radius.
    degrees_ -> number; angle of radius. 0 is at the top of the screen, with
        values increasing clockwise.
    
    Return point (x,y) on the circumference of a circle defined by center and
    radius along the given angle.
    """
    radians_ = radians(degrees_ - 90)
    x = center[0] + radius * cos(radians_)
    y = center[1] + radius * sin(radians_)
    return x,y
