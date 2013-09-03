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
__author__ = 'Gummbum, (c) 2011-2013'

__doc__ = """spatialhash.py - High performance spatial hash for spatial
partitioning and fast collision detection.

Objects (other than geometry.LineGeometry) must have a pygame Rect attribute.
Optionally, objects may have a collided static method attribute for lower-level
collision detection (see the gummworld2.geometry module).

Objects that are outside the world bounding rect are ignored by add().

This module is derived from the article and source code written by Conkerjo at
http://conkerjo.wordpress.com/2009/06/13/spatial-hashing-implementation-for-fast-2d-collisions/.
"""

import time
from math import ceil
from weakref import WeakKeyDictionary

import pygame
from pygame.locals import Rect

from gummworld2 import geometry


class SpatialHash(object):
    
    def __init__(self, world_rect, cell_size):
        ## Must inflate world rect by 1. This is because pygame rects consider
        ## the right and bottom borders to have zero units width. But the
        ## hashing calculates those as one unit width. Thus, taking pygame
        ## rect space at face value will attempt to access non-existant buckets
        ## at the corner cases.
        world_rect = world_rect.inflate(1,1)
        
        self.rect = Rect(world_rect)
        self.bounds = (
            world_rect[0],
            world_rect[1],
            world_rect[0] + world_rect[2],
            world_rect[1] + world_rect[3],
        )
        self.cell_size = int(cell_size)
        
        self.rows = int(ceil(world_rect.h / float(cell_size)))
        self.cols = int(ceil(world_rect.w / float(cell_size)))
        self.buckets = [[] for i in range(self.rows*self.cols)]
        ## cell_ids = {obj1:[cells...], obj2:[cells...], ...}
        self.cell_ids = WeakKeyDictionary()
        
        self.num_buckets = len(self.buckets)
        
        self.coll_tests = 0
        self._temp_rect = pygame.Rect(0,0,0,0)
    
    @property
    def objects(self):
        """Return the entire list of objects.
        """
        return self.cell_ids.keys()
    
    def add(self, obj):
        """Add or re-add obj. Return True if in bounds, else return False.
        
        If this method returns False then the object is completely out of
        bounds and cannot be stored in this space.
        
        Note that when obj changes its position, you must add it again so that
        its cell membership is updated. This method first removes the object if
        it is already in the spatial hash.
        """
        try:
            cell_ids = self.intersect_indices(obj.rect)
        except AttributeError:
            rect = self._get_rect_for_line(obj)
            cell_ids = self.intersect_indices(rect)
        if obj in self.cell_ids and cell_ids == self.cell_ids[obj]:
            return cell_ids == True
        self.remove(obj)
        buckets = self.buckets
        for idx in cell_ids:
            buckets[idx].append(obj)
        self.cell_ids[obj] = cell_ids
        return cell_ids == True
    
    def remove(self, obj):
        """Remove obj.
        """
        buckets = self.buckets
        cell_ids = self.cell_ids
        if obj in cell_ids:
            for cell_id in cell_ids[obj][:]:
## FIXED ... =P  problem was this line ^^^^ remove while iterating.
##
##  File "C:\cygwin\home\bw\devel\python\multifac\pyweek13\gamelib\gummworld2\spatialhash.py", line 67, in remove
##    if cell_id: buckets[cell_id].remove(obj)
##ValueError: list.remove(x): x not in list
                buckets[cell_id].remove(obj)
##superfluous...
##                cell_ids[obj].remove(cell_id)
##            if len(cell_ids[obj]) == 0:
##                del cell_ids[obj]
            del cell_ids[obj]
    
    def get_nearby_objects(self, obj):
        """Return a list of objects that share the same cells as obj.
        """
        nearby_objs = []
        try:
            cell_ids = self.intersect_indices(obj.rect)
        except AttributeError:
            rect = self._get_rect_for_line(obj)
            cell_ids = self.intersect_indices(rect)
        buckets = self.buckets
        for cell_id in cell_ids:
            nearby_objs.extend(buckets[cell_id])
        return list(set(nearby_objs))
    
    def get_cell(self, cell_id):
        """Return the cell stored at bucket index cell_id.
        
        The returned cell is a list of objects. None is returned if a cell does
        not exist for cell_id.
        """
        try:
            return self.buckets[cell_id]
        except:
            return None
    
    def index(self, cell):
        """Return the bucket index of cell.
        
        Returns None if cell does not exist in buckets.
        
        Note that SpatialHash.buckets.index(cell) does *NOT* work because
        list.index() tests equality, not identity.
        """
        for i,c in enumerate(self.buckets):
            if c is cell:
                return i
    
    def index_at(self, x, y):
        """Return the cell_id of the cell that contains point (x,y).
        
        None is returned if point (x,y) is not in bounds.
        """
        cell_size = self.cell_size
        rect = self.rect
        idx = ((x-rect[0])//cell_size) + ((y-rect[1])//cell_size) * self.cols
        return int(idx) if -1<idx<self.num_buckets else None
    
    def intersect_indices(self, rect):
        """Return list of cell ids that intersect rect.
        """
        # Not pretty, but these ugly optimizations shave 50% off run-time
        # versus function calls and attributes. This method is called by add(),
        # which gets called whenever an object moves.
        
        # return value
#        cell_ids = set()
        cell_ids = {}
        
        # pre-calculate bounds
        left = rect[0]
        top = rect[1]
        right = left + rect[2]
        bottom = top + rect[3]
        wl,wt,wr,wb = self.bounds
        if left < wl: left = wl
        if top < wt: top = wt
        if right > wr: right = wr
        if bottom > wb: bottom = wb
        cell_size = self.cell_size
        
        # pre-calculate loop ranges
        lrange = range
        x_range = lrange(left, right, cell_size) + [right]
        y_range = lrange(top, bottom, cell_size) + [bottom]
        
        # misc speedups
        cols = self.cols
#        cell_ids_add = cell_ids.add
        
        for x in x_range:
            for y in y_range:
                cell_id = x//cell_size + y//cell_size * cols
#                cell_ids_add(cell_id)
                cell_ids[cell_id] = 1
        
#        return list(cell_ids)
        return cell_ids.keys()
    
    def intersect_objects(self, rect):
        """Return list of objects whose rects intersect rect.
        """
        objs = {}
        colliderect = rect.colliderect
        rg = geometry.RectGeometry(*rect[:])
        for cell_ids in self.intersect_indices(rect):
            for o in self.get_cell(cell_ids):
                try:
                    if colliderect(o.rect):
                        try:
                            if o.collided(o, rg, True):
                                objs[o] = 1
                        except AttributeError:
                            objs[o] = 1
                except AttributeError:
                    try:
                        if o.collided(o, rg, True):
                            objs[o] = 1
                    except AttributeError:
                        pass
        return list(objs)
    
    def get_cell_grid(self, cell_id):
        """Return the (col,row) coordinate for cell id.
        """
        cell_size = self.cell_size
        cols = self.cols
        x = cell_id // cols
        y = cell_id - x * cols
        return x,y
    
    def get_cell_pos(self, cell_id):
        """Return the world coordinates for topleft corner of cell.
        """
        x,y = self.get_cell_grid(cell_id)
        cell_size = self.cell_size
        rect = self.rect
        return x*cell_size+rect.left, y*cell_size+rect.top
    
    def collideany(self, obj):
        """Return True if obj collides with any other object, else False.
        """
#        collided = self._extended_collided
        for other in self.get_nearby_objects(obj):
            if other is obj:
                continue
#            if collided(obj, other):
#                return True
            try:
                if obj.rect.colliderect(other.rect):
                    try:
                        if obj.collided(obj, other, True):
                            return True
                    except AttributeError:
                            return True
            except AttributeError:
                try:
                    if obj.collided(obj, other, True):
                        return True
                except AttributeError:
                    pass
        return False
    
    def collide(self, obj):
        """Return list of objects that collide with obj.
        """
        collisions = []
        append = collisions.append
#        collided = self._extended_collided
        for other in self.get_nearby_objects(obj):
            if other is obj:
                continue
#            if collided(obj, other):
#                append(other)
            try:
                if obj.rect.colliderect(other.rect):
                    try:
                        if obj.collided(obj, other, True):
                            append(other)
                    except AttributeError:
                            append(other)
            except AttributeError:
                try:
                    if obj.collided(obj, other, True):
                        append(other)
                except AttributeError:
                    pass
        return collisions
    
    def collidealldict(self, rect=None):
        """Return dict of all collisions.
        
        If rect is specified, only the cells that intersect rect will be
        checked.
        
        The contents of the returned dict are: {obj : [other1,other2,...],...}
        """
        collisions = {}
        self.coll_tests = 0
        if rect:
            buckets = self.buckets
            cells = [buckets[i] for i in self.intersect_indices(rect)]
        else:
            cells = self.buckets
        tests = 0
        for cell in cells:
            for obj in cell:
                for other in cell:
                    if other is obj:
                        continue
                    tests += 1
                    try:
                        if obj.rect.colliderect(other.rect):
                            try:
                                if obj.collided(obj, other, True):
                                    try:
                                        collisions[obj].append(other)
                                    except KeyError:
                                        collisions[obj] = [other]
                            except AttributeError:
                                    try:
                                        collisions[obj].append(other)
                                    except KeyError:
                                        collisions[obj] = [other]
                    except AttributeError:
                        try:
                            if obj.collided(obj, other, True):
                                try:
                                    collisions[obj].append(other)
                                except KeyError:
                                    collisions[obj] = [other]
                        except AttributeError:
                            pass
        self.coll_tests = tests
        return collisions
    
    def collidealllist(self, rect=None):
        """Return list of all collisions.
        
        If rect is specified, only the cells that intersect rect will be
        checked.
        
        The contents of the returned list are: [(obj,other),...]
        """
        collisions = {}
        if rect:
            buckets = self.buckets
            cells = [buckets[i] for i in self.intersect_indices(rect)]
        else:
            cells = self.buckets
        tests = 0
        for cell in cells:
            for obj in cell:
                for other in cell:
                    if other is obj:
                        continue
                    tests += 1
                    try:
                        if obj.rect.colliderect(other.rect):
                            try:
                                if obj.collided(obj, other, True):
                                    collisions[(obj,other)] = 1
#                                    collisions[(other,obj)] = 1
                            except AttributeError:
                                    collisions[(obj,other)] = 1
#                                    collisions[(other,obj)] = 1
                    except AttributeError:
                        try:
                            if obj.collided(obj, other, True):
                                collisions[(obj,other)] = 1
                                collisions[(other,obj)] = 1
                        except AttributeError:
                            pass
        self.coll_tests = tests
        return collisions.keys()
    
    def collideallflatlist(self, rect=None):
        """Return flat list of all collisions.
        
        If rect is specified, only the cells that intersect rect will be
        checked.
        
        The contents of the returned list are: [obj1,other1,obj2,other2...]
        """
        collisions = []
        append = collisions.append
        if rect:
            buckets = self.buckets
            cells = [buckets[i] for i in self.intersect_indices(rect)]
        else:
            cells = self.buckets
        tests = 0
        for cell in cells:
            for obj in cell:
                for other in cell:
                    if other is obj:
                        continue
                    tests += 1
                    try:
                        if obj.rect.colliderect(other.rect):
                            try:
                                if obj.collided(obj, other, True):
                                    append(obj)
                                    append(other)
                            except AttributeError:
                                    append(obj)
                                    append(other)
                    except AttributeError:
                        try:
                            if obj.collided(obj, other, True):
                                append(obj)
                                append(other)
                        except AttributeError:
                            pass
        self.coll_tests = tests
        return collisions
    
##    @staticmethod
## why did I make this a static method?
    def clear(self):
        """Clear all objects.
        """
        for cell in self.buckets:
            del cell[:]
    
    def iterobjects(self):
        """Returns a generator that iterates over all objects.
        
        Invoking a SpatialHash object as an iterator produces the same behavior
        as iterobjects().
        """
        for obj in self.cell_ids:
            yield obj
    
    def itercells(self):
        """Returns a generator that iterates over all cells.
        """
        for cell in self.buckets:
            yield cell
    
    def _extended_collided(obj, other):
        """Deprecated - moved inline for speed
        """
        try:
            if obj.rect.colliderect(other.rect):
                try:
                    return obj.collided(obj, other, True)
                except AttributeError:
                        return True
            else:
                return False
        except AttributeError:
            try:
                return obj.collided(obj, other, True)
            except AttributeError:
                return False
    
    def _get_rect_for_line(self, obj):
        """Lines don't have a rect attribute. Use self._temp_rect to fudge it.
        """
        points = obj.points
        rect = self._temp_rect
#        x1 = points[0]
#        y1 = points[1]
#        x2 = points[2]
#        y2 = points[3]
        x1,y1 = points[0]
        x2,y2 = points[1]
        if x1 > x2:
            t = x1
            x1 = x2
            x2 = t
        if y1 > y2:
            t = y1
            y1 = y2
            y2 = t
        rect.topleft = x1,y1
        rect.width = x2 - x1
        rect.height = y2 - y1
        return rect
    
    def __iter__(self):
        for obj in self.cell_ids:
            yield obj
    
    def __contains__(self, obj):
        return obj in self.cell_ids
    
    def __len__(self):
        return len(self.objects)
    
    def __str__(self):
        return '<%s(%s,%s)>' % (
            self.__class__.__name__,
            str(self.rect),
            str(self.cell_size),
        )
    
    def __repr(self):
        return self.__str__()


if __name__ == '__main__':
    class Obj(object):
        def __init__(self, x, y):
            self.rect = Rect(x,y,4,4)
        def __str__(self):
            return '<%s(%d,%d)>' % (
                self.__class__.__name__,
                self.rect.x,
                self.rect.y,
            )
        def __repr__(self):
            return self.__str__()
    pygame.init()
    world_rect = Rect(0,0,180,180)
    print 'World rect:',world_rect
    cell_size = 30
    shash = SpatialHash(world_rect, cell_size)
    print 'SpatialHash:',shash,'rows',shash.rows,'cols',shash.cols
    print shash.rows,shash.cols,len(shash.buckets)
    o = Obj(15,15)
    shash.add(o)
    assert o in shash
    assert shash.collideany(o) == False
    shash.add(Obj(16,15))
    shash.add(Obj(25,15))
    shash.add(Obj(30,15))
    shash.add(Obj(40,15))
    shash.add(Obj(15,40))
    assert shash.collideany(o)
    print shash.collide(o)
    print shash.collidealldict()
    print shash.collidealllist()
    print shash.intersect_indices(Rect(0,0,cell_size,cell_size))
    print shash.intersect_indices(Rect(0,30,cell_size,cell_size))
    print 'Objects 1 (__iter__):'
    for obj in shash:
        print obj
    print 'Objects 2 (iterobjects):'
    for obj in shash.iterobjects():
        print obj
    print 'Objects 3 (objects):'
    for obj in shash.objects:
        print obj
    print 'Cell position:'
    for i in range(len(shash.buckets)):
        print i,shash.get_cell_grid(i),shash.get_cell_pos(i)
    print 'Nearby objects:'
    print '  Reference:', o,shash.cell_ids[o]
    for obj in shash.get_nearby_objects(o):
        print '  nearby:',obj,shash.cell_ids[obj]
    
    screen = pygame.display.set_mode(world_rect.size)
    draw_line = pygame.draw.line
    draw_rect = pygame.draw.rect
    color = pygame.Color('darkgrey')
    left,right,top,bottom = world_rect.left,world_rect.right,world_rect.top,world_rect.bottom
    fill_rect = Rect(0,0,shash.cell_size,shash.cell_size)
    while 1:
        pygame.event.clear()
        screen.fill((0,0,0))
        minx = -1
        miny = -1
        for cell_id,cell in enumerate(shash.itercells()):
            x,y = shash.get_cell_pos(cell_id)
            if x > minx:
                minx = x
                p1 = x,top
                p2 = x,bottom
                draw_line(screen, color, p1, p2)
            if y > miny:
                miny = y
                p1 = left,y
                p2 = right,y
                draw_line(screen, color, p1, p2)
        x,y = pygame.mouse.get_pos()
        row,col = shash.get_cell_grid(shash.index_at(x,y))
        fill_rect.topleft = col*shash.cell_size,row*shash.cell_size
        screen.fill((0,255,255), fill_rect)
        for o in shash.objects:
            draw_rect(screen, (0,0,255), o.rect)
        pygame.display.flip()
