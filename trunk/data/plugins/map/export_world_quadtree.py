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


__doc__ = """export_world_quadtree.py - A quadtree-to-text exporter.

This plugin is required by world_editor.py, and possibly other scripts, to
export quadtree entities to a text file.

Shapes supported by this plugin are: RectGeometry, CircleGeometry, and
PolyGeometry.

The values saved are those needed for each shape-class's constructor, plus a
block of arbitrary user data.

Example usage:
    export_script = data.filepath('plugins', 'map/export_world_quadtree.py')
    entities = State.world.entity_branch.keys()
    fh = open('entities.txt', 'wb')
    locals_dict = {
        'entities' : entities,
        'fh' : fh,
    }
    execfile(export_script, {}, locals_dict)
"""


from urllib import quote

import pygame

from gamelib.geometry import RectGeometry, CircleGeometry, PolyGeometry


if 'entities' not in locals():
    raise pygame.error, 'local name "entities" missing'
if 'fh' not in locals():
    raise pygame.error, 'local name "fh" missing'

if not isinstance(entities, (list,tuple)) and not hasattr(entities, '__iter__'):
    raise pygame.error, 'entities must be iterable'
if not isinstance(fh, file):
    raise pygame.error, 'fh must be a file handle'

for entity in entities:
    if isinstance(entity, RectGeometry):
        # format:
        # rect x y w h
        # user_data ...
        x,y = entity.rect.topleft
        w,h = entity.rect.size
        user_data = ''
        if hasattr(entity, 'user_data'):
            user_data = quote(entity.user_data)
        
        fh.write('rect %d %d %d %d\n' % (x, y, w, h))
        fh.write('user_data ' + user_data + '\n')
    
    elif isinstance(entity, CircleGeometry):
        # format:
        # circle centerx centery radius
        # user_data ...
        x,y = entity.position
        radius = entity.radius
        user_data = ''
        if hasattr(entity, 'user_data'):
            user_data = quote(entity.user_data)
        
        fh.write('circle %d %d %d\n' % (x,y,radius))
        fh.write('user_data ' + user_data + '\n')
    
    elif isinstance(entity, PolyGeometry):
        # format:
        # poly centerx centery rel_x1 rel_y1 rel_x2 rel_y2 rel_x3 rel_y3...
        # user_data ...
        #
        # Note: x and y are relative to the containing rect's topleft.
        center = entity.rect.center
        x,y = entity.rect.topleft
        w,h = entity.rect.size
        user_data = ''
        if hasattr(entity, 'user_data'):
            user_data = quote(entity.user_data)
        
        fh.write('poly')
        fh.write(' %d %d' % center)
        for x1,y1 in entity.points:
            fh.write(' %d %d' % (x1-x,y1-y))
        fh.write('\n')
        fh.write('user_data ' + user_data + '\n')

    else:
        print 'unsupported type:', entity.__class__.__name__
