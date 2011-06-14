from math import ceil
from weakref import WeakKeyDictionary

import pygame
from pygame.locals import Rect


class SpatialHash(object):
    
    def __init__(self, world_rect, cell_size):
        self.rect = Rect(world_rect)
        self.cell_size = cell_size
        
        ## TODO: should raise exception if rows or cols == 0.
        self.rows = int(ceil(world_rect.w / float(cell_size)))
        self.cols = int(ceil(world_rect.h / float(cell_size)))
        self.buckets = [[] for i in range(self.rows*self.cols)]
        self.cell_ids = WeakKeyDictionary()
        
        self.coll_tests = 0
    
    @property
    def objects(self):
        return self.cell_ids.keys()
    
    def add(self, obj):
        """Add or re-add obj. Return True if in bounds, else return False.
        
        If obj changes its position, you must add it. obj will first be removed
        if it is already in the spatial hash.
        """
        self.remove(obj)
        buckets = self.buckets
        cell_ids = self.intersect(obj.rect)
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
            for cell_id in cell_ids[obj]:
                buckets[cell_id].remove(obj)
    
    def get_nearby(self, obj):
        """Return list of objects that share the same cells as obj.
        """
        nearby_objs = []
        cell_ids = self.intersect(obj.rect)
        buckets = self.buckets
        for cell_id in cell_ids:
            nearby_objs.extend(buckets[cell_id])
        return nearby_objs
    
    def get_cell(self, cell_id):
        return self.buckets[cell_id]
    
    def get_cell_id(self, cell):
        """Return the bucket index of cell.
        
        Returns None if cell does not exist in buckets.
        
        Note that SpatialHash.buckets.index(cell) does *NOT* work because
        list.index() tests equality, not identity.
        """
        for i,c in enumerate(self.buckets):
            if c is cell:
                return i
    
    def get_cell_id_at(self, x, y):
        """Return the id of the cell that contains point (x,y).
        """
        cell_size = self.cell_size
        left,top = self.rect.topleft
        cols = self.cols
        return ((x-left)//cell_size) + ((y-top)//cell_size) * cols
    
    def intersect(self, rect):
        """Return list of cell ids that intersect rect.
        """
        cell_ids = []
        crect = self.rect.clip(rect)
        cell_size = self.cell_size
        top = crect.top
        bottom = cell_size * int(ceil(crect.bottom/float(cell_size)))
        left = crect.left
        right = cell_size * int(ceil(crect.right/float(cell_size)))
        for x in range(left, right, cell_size):
            for y in range(top, bottom, cell_size):
                cell_id = self.get_cell_id_at(x,y)
                if cell_id not in cell_ids:
                    cell_ids.append(cell_id)
        return cell_ids
    
    def get_cell_pos(self, cell_id):
        """Return the world coordinates for topleft corner of cell.
        """
        cell_size = self.cell_size
        left,top = self.rect.topleft
        cols = self.cols
        y = cell_id // cols
        x = cell_id - y * cols
        return x*cell_size, y*cell_size
    
    def collideany(self, obj):
        """Return True if obj collides with any other object, else False.
        """
        collided = extended_collided
        for other in self.get_nearby(obj):
            if other is obj:
                continue
            if collided(obj, other):
                return True
        return False
    
    def collidealldict(self):
        """Return dict of all collisions.
        
        {obj : [other1,other2,...],...}
        """
        collisions = {}
        self.coll_tests = 0
        collided = extended_collided
        for cell in self.buckets:
            for obj in cell:
                for other in cell:
                    if other is obj:
                        continue
                    self.coll_tests += 1
                    if collided(obj, other):
                        if obj not in collisions:
                            collisions[obj] = []
                        collisions[obj].append(other)
        return collisions
    
    def collidealllist(self):
        """Return list of all collisions.
        
        [(obj,other),...]
        """
        collisions = set()
        self.coll_tests = 0
        collided = extended_collided
        for cell in self.buckets:
            for obj in cell:
                for other in cell:
                    if other is obj:
                        continue
                    self.coll_tests += 1
                    if collided(obj, other):
                        c1 = (obj,other)
                        c2 = (other,obj)
                        collisions.add(c1)
                        collisions.add(c2)
        return list(collisions)
    
    def collide(self, obj):
        """Return list of collisions with obj.
        """
        collisions = []
        collided = extended_collided
        for other in self.get_nearby(obj):
            if other is obj:
                continue
            if collided(obj, other):
                collisions.append(other)
        return collisions
            
    
    def clear(self):
        """Clear all objects.
        """
        for cell in self.buckets.values():
            del cell[:]
    
    def __contains__(self, obj):
        return obj in self.cell_ids
    
    def iterobjects(self):
        """Returns a generator that iterates over all objects.
        """
        for obj in self.objects:
            yield obj
    
    def itercells(self):
        """Returns a generator that iterates over all cells.
        """
        for cell in self.buckets:
            yield cell
    
    def __iter__(self):
        for obj in self.objects:
            yield obj
    
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


def extended_collided(obj, other):
    if obj.rect.colliderect(other.rect):
        if hasattr(obj, 'collided') and hasattr(other, 'collided'):
            return obj.collided(obj, other)
        else:
            return True
    else:
        return False


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
    world_rect = Rect(0,0,100,100)
    cell_size = 32
    shash = SpatialHash(world_rect, cell_size)
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
    print shash.intersect(Rect(0,0,cell_size,cell_size))
    print shash.intersect(Rect(0,30,cell_size,cell_size))
