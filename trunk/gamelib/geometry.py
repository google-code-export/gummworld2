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


__doc__ = """geometry.py - Geometry module for Gummworld2.

Geometry classes and functions.
"""


from math import atan2, cos, sin, pi, radians

import pygame


class Ellipse(object):
    
    def __init__(self, origin, radius_x, radius_y):
        """Construct an instance of Ellipse.
        
        The origin argument is a sequence of two numbers representing the origin
        (x,y).
        
        The radius_x argument is a number representing the radius along x-axis.
        
        The radius_y argument is a number representing the radius along y-axis.
        """
        self.origin = origin
        self.radius_x = radius_x
        self.radius_y = radius_y
        
        self._points = None
        self._dirty = True
    
    @property
    def origin(self):
        """Set or get origin."""
        return self._origin
    @origin.setter
    def origin(self, val):
        self._origin = val
        self._dirty = True
        
    @property
    def radius_y(self):
        """Set or get radius_y."""
        return self._radius_y
    @radius_y.setter
    def radius_y(self, val):
        self._radius_y = val
        self._dirty = True
        
    @property
    def radius_x(self):
        """Set or get radius_x."""
        return self._radius_x
    @radius_x.setter
    def radius_x(self, val):
        self._radius_x = val
        self._dirty = True
        
    def draw(self, surface, color, arcs=360):
        """Draw an ellipse on a pygame surface in the specified color.
        
        The surface argument is the target pygame surface.
        
        The color argument is the pygame color to draw in.
        
        The arcs argument is the number of points in the circumference to draw;
        normally 360 or 720 will suffice. More than 720 will draw many duplicate
        pixels.
        """
        if not self._dirty:
            points = self._points
        else:
            points = self.plot(arcs)
        pygame.draw.lines(surface, color, True,
            [(int(round(x)),int(round(y))) for x,y in points])
        
    def plot(self, arcs=360):
        """Plot the circumference of an ellipse and return the points in a list.
        
        The arcs argument is the number of points in the circumference to
        generate; normally 360 or 720 will suffice. More than 720 will result in
        many duplicate points.
        
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
        """Plot a point on the circumference of an ellipse at the specified angle.
        The point is returned as an (x,y) tuple.
        
        The angle argument is the angle in degrees from the origin. The angle 0
        and 360 are oriented at the top of the screen, and increase clockwise.
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
    """Calculate the angle between the vector defined by end points (origin,point)
    and the Y axis. All input and output values are in terms of pygame screen
    space. Returns degrees as a float.
    
    The origin argument is a sequence of two numbers representing the origin
    point.
    
    The point argument is a sequence of two numbers representing the end point.
    
    The angle 0 and 360 are oriented at the top of the screen, and increase
    clockwise.
    """
    x1,y1 = origin
    x2,y2 = end_point
    return (atan2(y2-y1, x2 - x1) * 180.0 / pi + 90.0) % 360.0


def distance(a, b):
    """Calculate the distance between points a and b. Returns distance as a float.
    
    The a argument is a sequence representing one end point (x1,y1).
    
    The b argument is a sequence representing the other end point (x2,y2).
    """
    x1,y1 = a
    x2,y2 = b
    diffx = x1 - x2
    diffy = y1 - y2
    return (diffx*diffx) ** 0.5 + (diffy*diffy) ** 0.5


def lines_intersection(line_1, line_2):
    """Determine the intersection point of the line segment defined by line_1 with
    the line segment defined by line_2.  Returns a tuple (x,y) representing the
    point of intersection.

    The line_1 argument is a sequence representing two end points of the first
    line ((x1,y1),(x2,y2)).
    
    The line_2 argument is a sequence representing two end points of the second
    line ((x3,y3),(x4,y4)).
    
    If no point of intersection is found, (False,False) is returned.
    
    If the lines coincide, in which case all points intersect, (True,True) is
    returned.
    
    This function always returns a tuple. This is intended to simplify handling
    the return data type. The following is an example of processing the possible
    return values.
    
        x,y = lines_intersection(A, B)
        if x is True: print 'lines coincide'
        elif x is False: print 'no intersection'
        else: print 'x,y is a point'
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
    """Calculate the point on the circumference of a circle defined by center and
    radius along the given angle. Returns a tuple (x,y).
    
    The center argument is a representing the origin of the circle.
    
    The radius argument is a number representing the length of the radius.
    
    The degrees_ argument is a number representing the angle of radius from
    origin. The angles 0 and 360 are at the top of the screen, with values
    increasing clockwise.
    """
    radians_ = radians(degrees_ - 90)
    x = center[0] + radius * cos(radians_)
    y = center[1] + radius * sin(radians_)
    return x,y
