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


__doc__ = """import_world_quadtree.py - A world entity importer.

This plugin is required by world_editor.py, and possibly other scripts, to
import world entities from a text file.

Shapes supported by this plugin are specified by passing in dict entries in the
locals() argument to execfile. The keys are 'rect_cls', 'poly_cls', and
'circle_cls' with corresponding class values. The constructor parameters must
have the same form as geometry.RectGeometry, et al.

The values imported are those needed for each shape-class's constructor, plus a
block of arbitrary user data which will be placed in the shape instance's
user_data attribute.

Example usage:
    import_script = data.filepath('plugins', 'map/import_world_quadtree.py')
    fh = open('entities.txt', 'rb')
    locals_dict = {
        'fh'         : fh,
        'rect_cls'   : RectGeom,
        'poly_cls'   : PolyGeom,
        'circle_cls' : CircleGeom,
    }
    execfile(import_script, {}, locals_dict)
    entities = locals_dict['entities']
    State.world.add(*entities)
"""


from urllib import unquote

import pygame

from gamelib.geometry import RectGeometry, CircleGeometry, PolyGeometry


if 'fh' not in locals():
    raise pygame.error, 'local name "fh" missing'

if 'rect_cls' not in locals():
    raise pygame.error, 'local name "rect_cls" missing'
if not issubclass(rect_cls, RectGeometry):
    raise pygame.error, 'local name "rect_cls" must be a class'
if 'poly_cls' not in locals():
    raise pygame.error, 'local name "poly_cls" missing'
if not issubclass(poly_cls, PolyGeometry):
    raise pygame.error, 'local name "poly_cls" must be a class'
if 'circle_cls' not in locals():
    raise pygame.error, 'local name "circle_cls" missing'
if not issubclass(circle_cls, CircleGeometry):
    raise pygame.error, 'local name "circle_cls" must be a class'

if not isinstance(fh, file):
    raise pygame.error, 'fh must be a file handle'

entities = []

line_num = 0

for line in fh:
    line_num += 1
    
    parts = line.split(' ')
    if len(parts) < 1:
        continue
    what = parts[0]
    if what == 'user_data':
        # User data.
        entity.user_data = unquote(' '.join(parts[1:]))
    
    elif what == 'rect':
        # format:
        # rect x y w h
        x,y = int(parts[1]), int(parts[2])
        w,h = int(parts[3]), int(parts[4])
        
        entity = rect_cls(x, y, w, h)
        entities.append(entity)

    elif what == 'circle':
        # format:
        # circle centerx centery radius
        x,y = int(parts[1]), int(parts[2])
        radius = float(parts[3])
        
        entity = circle_cls((x,y), radius)
        entities.append(entity)
    
    elif what == 'poly':
        # format:
        # poly centerx centery rel_x1 rel_y1 rel_x2 rel_y2 rel_x3 rel_y3...
        #
        # Note: x and y are relative to the containing rect's topleft.
        center = int(parts[1]), int(parts[2])
        points = []
        for i in range(3, len(parts), 2):
            points.append(( int(parts[i]), int(parts[i+1]) ))
        entity = poly_cls(points, center)
        entities.append(entity)
        
    else:
        raise pygame.error, 'line %d: keyword "%s" unexpected' % (line_num,what)
