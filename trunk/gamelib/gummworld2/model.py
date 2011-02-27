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


__doc__ = """model.py - Physics model for Gummworld2.

If pymunk is installed and can be imported, then the pymunk subclasses
WorldPymunk and various bodies will be created. Otherwise, only the classes
World and Object will be available.
"""

import os
import re
import urllib

import pygame
try:
    import pymunk
except:
    pymunk = None

try:
    from gummworld2 import quad_tree
    from gummworld2.geometry import RectGeometry, CircleGeometry, PolyGeometry
except:
    quad_tree = None

from gummworld2 import State, Vec2d, data, toolkit


class NoWorld(object):
    
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
    
    def add(self, *args):
        pass
    
    def step(self):
        pass


class Object(object):
    """An object model suitable for use as a Camera target or an autonomous
    object in World.
    
    Similar to pygame.sprite.Sprite, without the graphics and rect. Subclass
    this and extend.
    """
    
    def __init__(self, position=(0,0)):
        self._position = Vec2d(position)
        self._worlds = {}
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        p = self._position
        p.x,p.y = val
    
    def update(self, *args):
        pass
    
    def worlds(self):
        return self._worlds.keys()
    
    def kill(self):
        for w in self._worlds:
            w.remove(self)
        self._worlds.clear()


class World(object):
    """A container for model.Objects.
    
    Similar to pygame.sprite.AbstractGroup. Not compatible with
    pygame.sprite.Sprite.
    
    If you want the world to store pygame sprites, substitute a group and that
    has a rect attribute and step() method.
    """
    
    def __init__(self, rect):
        """rect is bounding box edges in pygame space"""
        self.rect = pygame.Rect(rect)
        self._object_dict = {}
    
    def add(self, *objs):
        """Add objects to the world."""
        for o in objs:
            self._object_dict[o] = 1
            if not hasattr(o, '_worlds'):
                o._worlds = {}
            o._worlds[self] = 1
    
    def remove(self, *objs):
        for o in objs:
            if o in self._object_dict:
                del self._object_dict[o]
            if hasattr(o, '_worlds') and self in o._worlds:
                del o._worlds[self]
    
    def objects(self):
        return self._object_dict.keys()
    
    def step(self):
        for o in self.objects():
            o.update()
    
    def __iter__(self):
        return iter(self.objects())
    
    def __contains__(self, obj):
        return obj in self._object_dict
    
    def __nonzero__(self):
        return (len(self._object_dict) != 0)
    
    def __len__(self):
        """len(group)
           number of sprites in group
    
           Returns the number of sprites contained in the group."""
        return len(self._object_dict)
    
    def __repr__(self):
        return "<%s(%d objects)>" % (self.__class__.__name__, len(self))


if quad_tree is not None:
    
    class QuadTreeObject(object):
        """An object model suitable for use as a Camera target or an autonomous
        object in QuadTreeWorld.
        """
        
        def __init__(self, rect, position=(0,0)):
            self.rect = pygame.Rect(rect)
            self._position = Vec2d(position)
        
        @property
        def position(self):
            return self._position
        @position.setter
        def position(self, val):
            p = self._position
            p.x,p.y = val
            self.rect.center = round(p.x), round(p.y)


    class WorldQuadTree(quad_tree.QuadTree):
        
        def step(self):
            pass


def export_world_quadtree(fh, entities):
    """A quadtree-to-text exporter.
    
    This function is required by world_editor.py, and possibly other scripts, to
    export quadtree entities to a text file.
    
    Geometry classes used by this plugin are: RectGeometry, CircleGeometry, and
    PolyGeometry.
    
    The values saved are those needed for each shape-class's constructor, plus a
    block of arbitrary user data. The user data is url-encoded.
    """
    
    if not isinstance(entities, (list,tuple)) and not hasattr(entities, '__iter__'):
        raise pygame.error, 'entities must be iterable'
    
    def quote(user_data):
        translated_data = []
        for line in user_data.split('\n'):
            line = line.rstrip('\r')
            line = re.sub(r'\\', '/', line)
            translated_data.append(line)
        quoted_data = '\n'.join(translated_data)
        quoted_data = urllib.quote(quoted_data)
        return quoted_data
    
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
            raise pygame.error, 'unsupported type: ' + entity.__class__.__name__
    
# export_world_quadtree


def import_world_quadtree(fh, rect_cls, poly_cls, circle_cls):
    """A world entity importer compatible with QuadTree.
    
    This function is required by world_editor.py, and possibly other scripts, to
    import world entities from a text file. It understands the format of files
    created by export_world_quadtree().

    Geometry classes used by this function to create shape objects are specified
    by the rect_cls, poly_cls, and circle_cls arguments. The constructor
    parameters must have the same signature as geometry.RectGeometry, et al.

    The values imported are those needed for each shape-class's constructor,
    plus a block of arbitrary user data which will be placed in the shape
    instance's user_data attribute.

    The user_data is also parsed for tilesheet info. Tilesets are loaded and
    returned as a dict of toolkit.Tilesheet, keyed by relative path to the
    image file.
    """
    
    if not issubclass(rect_cls, RectGeometry):
        raise pygame.error, 'argument "rect_cls" must be a subclass of geometry.RectGeometry'
    if not issubclass(poly_cls, PolyGeometry):
        raise pygame.error, 'argument "poly_cls" must be a subclass of geometry.PolyGeometry'
    if not issubclass(circle_cls, CircleGeometry):
        raise pygame.error, 'argument "circle_cls" must be a subclass of geometry.CircleGeometry'
    
    entities = []
    tilesheets = {}
    
    line_num = 0
    for line in fh:
        line_num += 1
        line = line.rstrip('\r\n')
        parts = line.split(' ')
        if len(parts) < 1:
            continue
        what = parts[0]
        if what == 'user_data':
            # User data format:
            # user_data url_encoded_string
            user_data = []
            # Unquote the user_data string and split it into lines.
            lines = urllib.unquote(' '.join(parts[1:])).split('\n')
            # Scan each line for tile info, load the tilesheets, and populate the
            # entity's user_data attribute.
            for line in lines:
                # Split into space-delimited tokens.
                parts = line.split(' ')
                if parts[0] == 'tile':
                    # Process the tile info entry. Format is:
                    # 0: tile
                    # 1: tile_id
                    # 2..end: relpath_of_image
                    file_path = ' '.join(parts[2:])
                    file_path = os.path.join(*file_path.split('/'))
                    if file_path not in tilesheets:
                        tilesheet = toolkit.load_tilesheet(file_path)
                        tilesheets[file_path] = tilesheet
                    # Join the parts and append to user_data.
                    line = ' '.join(parts[0:2] + [file_path])
                user_data.append(line)
            entity.user_data = '\n'.join(user_data)
        elif what == 'rect':
            # Rect format:
            # rect x y w h
            x,y = int(parts[1]), int(parts[2])
            w,h = int(parts[3]), int(parts[4])
            entity = rect_cls(x, y, w, h)
            entities.append(entity)
        elif what == 'circle':
            # Circle format:
            # circle centerx centery radius
            x,y = int(parts[1]), int(parts[2])
            radius = float(parts[3])
            entity = circle_cls((x,y), radius)
            entities.append(entity)
        elif what == 'poly':
            # Polygon format:
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
        
    return entities, tilesheets
    
# import_world_quadtree
    

if pymunk is not None:
    
    class WorldPymunk(pymunk.Space):
        """If pymunk is available use WorldPymunk. This WorldPymunk class sets up
        the pymunk space, and abstracts the step() method.
        """
        
        def __init__(self, rect):
            """left, bottom, right, top are bounding box edges in pygame space"""
            super(WorldPymunk, self).__init__()
            self.rect = pygame.Rect(rect)
        
        def step(self):
            super(WorldPymunk, self).step(State.dt)


    class CircleBody(pymunk.Body):
        """A pymunk.Circle with defaults for position, angle, velocity, radius,
        mass, and the shape.
        """
        
        def __init__(self, mass=1.0, radius=1.0,
            position=(0.0,0.0), angle=0.0, velocity=(0,0)):

            inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))
            super(CircleBody, self).__init__(mass, inertia)
            self.shape = pymunk.Circle(self, radius)

            self.position = position
            self.angle = angle
            self.velocity = velocity
