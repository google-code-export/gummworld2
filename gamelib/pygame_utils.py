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


"""pygame_utils.py - Collection of pygame utilities for Gummworld2.
"""


###Python imports
from math import sqrt, pow, pi, atan2, sin, cos, degrees, radians
import os
import re
import sys

import pygame
from pygame.locals import Color

try:
    ### Pygame imports
    import pygame
    from pygame.locals import MOUSEBUTTONDOWN, RLEACCEL
except ImportError, e:
    print 'ImportError: %s' % e
    print '    in file "%s"' % os.path.abspath(sys.argv[0])


def split_thousands(s, sep=','): 
    """insert a comma every thousands place"""
    if len(s) <= 3: return s
    return split_thousands(s[:-3], sep) + sep + s[-3:]


def sign(number):
    return number / abs(number)


def cw_corners(r):
    """return a tuple containing the corners of rect r in clockwise order
    starting with topleft
    """
    return r.topleft,r.topright,r.bottomright,r.bottomleft


def ccw_corners(r):
    """return a tuple containing the corners of rect r in counter-clockwise
    order starting with topleft
    """
    return r.topleft,r.bottomleft,r.bottomright,r.topright


def distance(a, b):
    """calculate the distance between points a and b
    
    Returns distance as a float.
    a and b should be float. a is point x1,y1, b is point x2,y2.
    """
    diffx = a[0] - b[0]
    diffy = a[1] - b[1]
#    return sqrt(pow(diffx,2) + pow(diffy,2))
    return (diffx*diffx) ** 0.5 + (diffy*diffy) ** 0.5


def fill_gradient(surface, color, gradient, rect=None, vertical=True, forward=True):
    """fill a surface with a gradient pattern
    Parameters:
    surface -> drawing surface
    color -> starting color
    gradient -> final color
    rect -> area to fill; default is surface's rect
    vertical -> True=vertical; False=horizontal
    forward -> True=forward; False=reverse
    
    Pygame recipe: http://www.pygame.org/wiki/GradientCode
    """
    if rect is None: rect = surface.get_rect()
    x1,x2 = rect.left, rect.right
    y1,y2 = rect.top, rect.bottom
    if vertical: h = y2-y1
    else:        h = x2-x1
    if forward: a, b = color, gradient
    else:       b, a = color, gradient
    rate = (
        float(b[0]-a[0])/h,
        float(b[1]-a[1])/h,
        float(b[2]-a[2])/h
    )
    fn_line = pygame.draw.line
    if vertical:
        for line in range(y1,y2):
            color = (
                min(max(a[0]+(rate[0]*(line-y1)),0),255),
                min(max(a[1]+(rate[1]*(line-y1)),0),255),
                min(max(a[2]+(rate[2]*(line-y1)),0),255)
            )
            fn_line(surface, color, (x1,line), (x2,line))
    else:
        for col in range(x1,x2):
            color = (
                min(max(a[0]+(rate[0]*(col-x1)),0),255),
                min(max(a[1]+(rate[1]*(col-x1)),0),255),
                min(max(a[2]+(rate[2]*(col-x1)),0),255)
            )
            fn_line(surface, color, (col,y1), (col,y2))


def _init_fonts():
    """Initializes the shared font cache."""
    global _fonts
    _fonts = dict(
        default = pygame.font.SysFont('Vera', 16),
        default_bold = pygame.font.SysFont('Vera', 16, True),
        gui = pygame.font.SysFont('Vera', 16),
        gui_bold = pygame.font.SysFont('Vera', 16, True),
)
_fonts = {}


def get_font(name='default'):
    """Return the named pygame.font.
    
    The named font is looked up in cached fonts. The font named 'default'
    is always available. See make_font() for adding custom fonts to the
    cache.
    """
    global _fonts
    if len(_fonts.keys()) == 0:
        _init_fonts()
    return _fonts[name]


def get_font_names():
    """Return a list of existing font names."""
    return _fonts.keys()


def make_font(name, file_name, font_size, bold=False, italic=False):
    """Create a pygame.font.Font from a file. Return the font object.
    
    An instance of pygame.font.Font is created and stored in a cache for
    retrieval by get_font(). Initially there is one font named 'default',
    which may be replaced by a custom font via this function if desired.
    Arguments mirror those of pygame.font.SysFont().
    """
    global _fonts
    if len(_fonts.keys()) == 0:
        _init_fonts()
    _fonts[name] = pygame.font.Font(file_name, font_size)
    if bold:
        _fonts[name].set_bold(True)
    if italic:
        _fonts[name].set_italic(True)
    return _fonts[name]


def make_sysfont(name, font_name, font_size, bold=False, italic=False):
    """Create a pygame.font.Font from system fonts. Return the font object.
    
    An instance of pygame.font.Font is created and stored in a cache for
    retrieval by get_font(). Initially there is one font named 'default',
    which may be replaced by a custom font via this function if desired.
    Arguments mirror those of pygame.font.SysFont().
    """
    global _fonts
    if len(_fonts.keys()) == 0:
        _init_fonts()
    _fonts[name] = pygame.font.SysFont(font_name, font_size, bold, italic)
    return _fonts[name]


def import_module(fullname):
    """Dynamically imports a module by name

    fullname is a string in any of these syntaxes:
    1. A file name in the Python path, with or without .py extension.
    2. Relative or absolute path and file, with or without .py extension. If
    path contains os.pathsep, the Python path is not used to locate the file.
    A relative path is relative to the current working directory.
    """
    if fullname.endswith('.py'):
        fullname = fullname[:-3]
    parts = re.split(r'[\\/]+', fullname)
    if len(parts) > 1:
        shortname = parts.pop()
        module_dir = os.pathsep.join(parts)
        sys.path.append(module_dir)
    else:
        shortname = fullname
        sys.path.append(os.getcwd())
    try:
        __import__(shortname)
    except ImportError:
        print "No %s.py found in module path:" % shortname
        for p in sys.path:
            print "   %s" % p
        sys.exit()
    return sys.modules[shortname]


def draw_text(image, text, pos=(0,0), font='default', fg=(254,254,254),
    bg=(-1,-1,-1), rect_attr=('left','top')):
    """Render text on the image in the named font.
    
    Text is rendered at pos in foreground color fg. Width and height of
    the rendered text is returned. rect_attr are the position attributes
    of the resulting rect to set equal to pos.
    """
    font = get_font(font)
    if type(fg) is tuple:
        fg = Color(*fg)
    elif type(fg) is not Color:
        fg = Color(fg)
    if type(bg) is tuple:
        if bg != (-1,-1,-1):
            bg = Color(*bg)
    elif type(bg) is not Color:
        bg = Color(bg)
    if bg == (-1,-1,-1):
        font_image = font.render(text, True, fg)
    else:
        font_image = font.render(text, True, fg, bg)
    font_rect = font_image.get_rect()
    for i in range(2):
        setattr(font_rect, rect_attr[i], pos[i])
    image.blit(font_image, font_rect)
    return font.size(text)


def circumference_point(center, radius, degrees_):
    """x,y on the circumference of a circle defined by center and radius"""
    radians_ = radians(degrees_ - 90)
    x = center[0] + radius * cos(radians_)
    y = center[1] + radius * sin(radians_)
    return x,y


def screen_angle(origin, point):
    """screen angle between a vector and Y axis from a common origin"""
    x1,y1 = origin
    x2,y2 = point
    return (atan2(y2-y1, x2 - x1) * 180.0 / pi + 90.0) % 360.0


def calc_line(p0, p1):
    """use Bresenham's algorithm to calculate a set of closed points forming a line
    
    Returns an array whose elements are the points of the line.
    
    Original calc_line code retrieved from:
    http://en.literateprograms.org/Bresenham's_line_algorithm_(Python)?oldid=16281
    """
    origin = x0,y0 = int(p0[0]),int(p0[1])
    x1,y1 = int(p1[0]),int(p1[1])
    points = []
    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0
    if y0 < y1:
        ystep = 1
    else:
        ystep = -1
    deltax = x1 - x0
    deltay = abs(y1 - y0)
    error = -deltax / 2
    y = y0
    for x in range(x0, x1 + 1): # add 1 to x1 so the range includes x1
        if steep:
            points.append((y,x))
        else:
            points.append((x,y))
        error = error + deltay
        if error > 0:
            y = y + ystep
            error = error - deltax
    if origin != points[0]:
        points.reverse()
    return points


def calculate_bezier(p, steps=30):
    """calculate a bezier curve from 4 control points
    
    Returns a list of the resulting points.
    
    The function uses the forward differencing algorithm described here: 
    http://www.niksula.cs.hut.fi/~hkankaan/Homepages/bezierfast.html
    
    This code taken from www.pygame.org/wiki/BezierCurve.
    """
    #
    t = 1.0 / steps
    temp = t*t
    #
    f = p[0]
    fd = 3 * (p[1] - p[0]) * t
    fdd_per_2 = 3 * (p[0] - 2 * p[1] + p[2]) * temp
    fddd_per_2 = 3 * (3 * (p[1] - p[2]) + p[3] - p[0]) * temp * t
    #
    fddd = fddd_per_2 + fddd_per_2
    fdd = fdd_per_2 + fdd_per_2
    fddd_per_6 = fddd_per_2 * (1.0 / 3)
    #
    points = []
    for x in range(steps):
        points.append(f)
        f = f + fd + fdd_per_2 + fddd_per_6
        fd = fd + fdd + fddd_per_2
        fdd = fdd + fddd
        fdd_per_2 = fdd_per_2 + fddd_per_2
    points.append(f)
    return points


def rot_center(image, angle):
    """rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = pygame.Rect(orig_rect)
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image


def sign(n):
    """return the sign of number n"""
    if n >= 0:
        return 1
    else:
        return -1


def plot_curve(p):
    """plot a curved path along one or more sets of control points
    
    p is a one-dimensional array of points in multiples of four: i.e.
    four points per curve.
    
    steps is the number of points desired. steps is weighted by the sum
    distance of each four points in order to yield approximately
    equidistant points.
    
    This code derived from www.pygame.org/wiki/BezierCurve.
    """
    plot = []
    for x in range((len(p)-1)/3):
        slice = p[3*x:3*x+4]
        dist = 0.0
        p0 = slice[0]
        for i in range(1,3):
            dist = max(dist, distance(p0, p[i]))
            p0 = p[i]
        n = 200
        b_points = calculate_bezier(slice, n)
        plot.extend(b_points)
    return plot


def load_image(name, colorkey=None, alpha=False):
    """load an image into memory"""
    if name in _IMAGE_CACHE:
        image = _IMAGE_CACHE[name].copy()
        image.set_alpha(_IMAGE_CACHE[name].get_alpha())
    else:
        try:
            image = pygame.image.load(name)
            _IMAGE_CACHE[name] = image
        except pygame.error, message:
            print 'Cannot load image:', name
            raise SystemExit, message
    if alpha:
        image = image.convert_alpha()
    else:
        image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()
_IMAGE_CACHE = {}


def wait_event(type=MOUSEBUTTONDOWN):
    while 1:
        e = pygame.event.wait()
        if e.type == type:
            return
