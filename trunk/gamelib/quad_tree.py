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


__doc__ = """quad_tree.py - A quad tree implementation for pygame.

Quick and dirty:
    
    # This code facsimile updates and draws the things that are on-screen.
    class ObjectWithRect(object):
        def __init__(self):
            self.rect = pygame.Rect(...)
    thing = ObjectWithRect()
    world = QuadTree(world_rect)
    world.add(thing)
    while 1:
        things = world.entities_in(camera_rect)
        for thing in things:
            things_that_moved = update_list(things)
        for thing in things_that_moved:
            world.add(thing)
        draw_list(things)

Thanks to:
    *   Dylan J. Raub for his excellent pygame demo, Quadtree test, after which
        this module has been fundamentally modeled. Visit the project page:
        http://www.pygame.org/project-Quadtree+test-1691-.html.
    *   Jonathan Fararis for his excellent Quadtrees paper on gamedev.net.
        Original URL: http://www.gamedev.net/reference/programming/features/quadtrees/
        Archive URL: http://archive.gamedev.net/reference/programming/features/quadtrees/
"""

import math
from random import randrange

import pygame
from pygame.locals import *


class QuadTreeNode(object):
    
    def __init__(self, parent, rect, branch_id=1):
        """Should be no need to manually construct these. The QuadTree
        constructor does this automatically.
        """
        self.root = parent.root
        self.parent = parent
        self.level = parent.level + 1
        self.rect = pygame.Rect(rect)
        self.branch_id = branch_id
##        print self.path
        self.branches = []
        self.entities = {}
        self.root.num_levels = max(self.level, self.root.num_levels)
        self._split()
    
    def _split(self):
        """Internal use. Split a node into four branches. For the root node, add
        the nine enhancement branches if worst_case is enabled.
        """
        if self.branch_id > 4:
            return
        rect = self.rect
        min_width,min_height = self.root.min_size
        half_width,half_height = rect.width//2, rect.height//2
        if half_width < min_width or half_height < min_height:
            return
        
        # Position and size the quarters.
        # Rect layout:
        #   r1 r2
        #   r3 r4
        (left,top),(right,bottom) = rect.topleft, rect.bottomright
        cx,cy = rect.center
        r1 = pygame.Rect(left,top, half_width,half_height)
        r2 = pygame.Rect(cx,top,   half_width,half_height)
        r3 = pygame.Rect(left,cy,  half_width,half_height)
        r4 = pygame.Rect(cx,cy,    half_width,half_height)
        # Parent rects aren't always evenly divisible. Increase size by one
        # pixel as needed.
        for r in (r2,r4):
            if r.right != rect.right:
                r.width += 1
        for r in (r3,r4):
            if r.bottom != rect.bottom:
                r.height += 1
        # Error checking.
        if __debug__:
            assert r1.bottomright == rect.center, (r1.bottomright, rect.center)
            assert r2.bottomright == (right,cy), (r2.bottomright,(right,cy))
            assert r3.bottomright == (cx,bottom), (r2.bottomright,(cx,bottom))
            assert r4.bottomright == (right,bottom), (r2.bottomright,(right,bottom))
        
        branches = self.branches
        branches.append(QuadTreeNode(self, r1, 1))
        branches.append(QuadTreeNode(self, r2, 2))
        branches.append(QuadTreeNode(self, r3, 3))
        branches.append(QuadTreeNode(self, r4, 4))
        
        if self.is_root and self.root.worst_case > 0:
            ## 3x3 catch-all for worst performance cases that would tend to load
            ## level 1 with entities. For example: entities that are a little
            ## outside of world bounds; entities that concurrently align on
            ## quad grid lines. These branches divide level 1 in parts by 3
            ## instead of 2.
            ##
            ## These are only tried by QuadTreeNode._add_internal() if none of
            ## the quad buckets on level 2 are a fit. However, they are searched
            ## for every lookup, and thus increase the general workload when not
            ## needed.
            WC = self.root.worst_case
            top2 = top + rect.height * 1 // 3
            top3 = top + rect.height * 2 // 3
            left2 = left + rect.width * 1 // 3
            left3 = left + rect.width * 2 // 3
            width3 = rect.width // 3
            height3 = rect.height // 3
            # Left 3.
            r1 = pygame.Rect(left-WC,top-WC,  width3+WC,height3+WC)
            r2 = pygame.Rect(left-WC,top2,    width3+WC,height3)
            r3 = pygame.Rect(left-WC,top3,    width3+WC,height3+WC)
            branches.append(QuadTreeNode(self, r1, 5))
            branches.append(QuadTreeNode(self, r2, 6))
            branches.append(QuadTreeNode(self, r3, 7))
            # Middle 3.
            r1 = pygame.Rect(left2,top-WC,  width3,height3+WC)
            r2 = pygame.Rect(left2,top2,    width3,height3)
            r3 = pygame.Rect(left2,top3,    width3,height3+WC)
            branches.append(QuadTreeNode(self, r1, 8))
            branches.append(QuadTreeNode(self, r2, 9))
            branches.append(QuadTreeNode(self, r3, 10))
            # Right 3.
            r1 = pygame.Rect(left3,top-WC, width3+WC,height3+WC)
            r2 = pygame.Rect(left3,top2,   width3+WC,height3)
            r3 = pygame.Rect(left3,top3,   width3+WC,height3+WC)
            branches.append(QuadTreeNode(self, r1, 11))
            branches.append(QuadTreeNode(self, r2, 12))
            branches.append(QuadTreeNode(self, r3, 13))
    
    def _add_internal(self, entity):
        """Internal use. Find the best fit node. Test collisions along the way.
        """
        root = self.root
        root.branch_visits_add += 1
        collided = root.collided
        collisions = root.collisions
        for other in self.entities:
            if collided(other, entity):
                collisions[other,entity] = 1
                collisions[entity,other] = 1
        
        # Find best fit.
        fit = None
        for b in self.branches:
            if b.rect.contains(entity.rect):
                fit = b
                break
        if fit:
            fit._add_internal(entity)
        else:
            self._keep(entity)
            for b in self.branches:
                b.test_collisions(entity)
            if self.branch_id > 4:
                for b in root.branches[:4]:
                    b.test_collisions(entity)
            elif not self.is_root:
                entity_rect = entity.rect
                for b in root.branches[4:]:
                    if self is b:
                        continue
                    b.test_collisions(entity)
    
    def _keep(self, entity):
        """Internal use. Keep the entity in this node.
        """
        self.root.entity_branch[entity] = self
        self.entities[entity] = 1
    
    def test_collisions(self, entity):
        """Kick off a recursive collision test starting with this node. It is
        usually not necessary to do this. It is done automatically when an
        entity is added.
        """
        if not self.rect.colliderect(entity.rect):
            return
        collided = self.root.collided
        collisions = self.root.collisions
        for other in self.entities:
            if collided(other, entity):
                collisions[other,entity] = 1
                collisions[entity,other] = 1
        for b in self.branches:
            b.test_collisions(entity)
    
    def _get_entities_recursive(self, rect, results):
        """Internal use. Recursively add entities to results if they collide
        with rect.
        """
        if self.rect.colliderect(rect):
            results.extend([e for e in self.entities if e.rect.colliderect(rect)])
            for b in self.branches:
                b._get_entities_recursive(rect, results)
    
    @property
    def path(self):
        """Return a string indicating branch_id's along the path from the root
        to this branch. This is a debugging/tuning aid.
        """
        this_branch = str(self.level) + ':' + str(self.branch_id)
        if self.is_root:
            return this_branch
        else:
            return '_'.join((self.parent.path, this_branch))
    
    def entities_per(self, results):
        """Recursively build a list of tuples in results. Each tuple contains
        the branch level, branch id, and number of entities. This is a debuggin/
        tuning aid.
        """
        this_branch = (self.level, self.branch_id, len(self.entities))
        results.append(this_branch)
        for b in self.branches:
            b.entities_per(results)
        return results
    
    @property
    def is_root(self):
        """True if this node is the root node.
        """
        return self is self.root
    
    @property
    def is_leaf(self):
        """True if this node is a leaf node (i.e., has no branches).
        """
        return len(self.branches) == 0


class QuadTree(QuadTreeNode):
    
    def __init__(self, rect, *entities, **kwargs):
        """QuadTree(rect, min_size=(128,128), worst_case=0,
        collide_rects=True, collide_entities=False, *entities)
        
        The QuadTree container efficiently stores objects, maintains
        collision info, and retrieves objects in an arbitrarily defined locale.
        
        The rect argument defines the quadtree's dimensions.
        
        The min_size argument defines the smallest quad size needed. The
        quadtree will be recursively subdivided until this limit is reached.
        
        The worst_case argument enables an enhancement to reduce the number of
        objects that default to level 1. A value greater than zero enables this
        enhancement, and represents the amount to extend the quadtree's bounds
        on each side.
        
        The collide_rects argument sets the collision detection behavior that
        relies on the object having a pygame.Rect instance variable.
        
        The collide_entities argument sets the collision detection behavior that
        relies on the object having a collided instance variable, which is a
        staticmethod that takes two entities as arguments.
        
        The entities argument is the entities to add.
        
        QuadTree subclasses QuadTreeNode. See the superclass for more methods.
        
        More detail on worst_case. Level 1 is expensive in terms of adding
        objects, since objects in level 1 are always involved in collisions
        detection, and many of those could be far away from the object being
        added. As few as 25 objects in level 1 can double the number of
        collision checks per add. Without this enhancement, such objects are:
        those that straddle quad boundaries; those positioned outside the
        quadtree bounds. The size of worst_case doesn't affect the size of the
        quadtree bounding rect, and using excessively large values does not
        incur a performance penalty. However, this feature adds nine branches
        to level 2 that are recursively walked by the quadtree algorithms. The
        lowdown: for large numbers of objects it is worth turning on
        worst_case; for only a few objects or quadtrees with two levels the
        overhead of nine more branches may not be worthwhile. Lastly, this
        choice may only be of importance if trying to implement a quadtree on a
        wimpy platform. Try it both ways and check instance variables coll_tests
        and branch_visits_add after each game update to decide.
        """
        valid_kw = 'min_size','worst_case','collide_rects','collide_entities'
        for kw in kwargs:
            if kw not in valid_kw:
                raise pygame.error,'invalid keyword '+kw
        self.root = self
        self.min_size = kwargs.get('min_size', (128,128))
        self.worst_case = kwargs.get('worst_case', 0)
        self.level = 0
        self.entity_branch = {}
        self.collisions = {}
        self.num_levels = 1
        
        self.coll_tests = 0
        self.branch_visits_add = 0
        
        self._collide_rects = kwargs.get('collide_rects', True)
        self._collide_entities = kwargs.get('collide_entities', False)
        self._set_collided()
        
        super(QuadTree, self).__init__(self, rect)
        self.add_list(entities)
    
    @property
    def collide_rects(self):
        return self._collide_rects
    @collide_rects.setter
    def collide_rects(self, val):
        self._collide_rects = val
        self._set_collided()
    
    @property
    def collide_entities(self):
        return self._collide_entities
    @collide_entities.setter
    def collide_entities(self, val):
        self._collide_entities = val
        self._set_collided()
    
    def _set_collided(self):
        if self._collide_rects and self._collide_entities:
            self._collided = self._collided_full
        elif self._collide_entities:
            self._collided = self._collided_entities
        else:
            self._collided = self._collided_rects
    
    def reset_counters(self):
        self.coll_tests = 0
        self.branch_visits_add = 0
    
    def add(self, *entities):
        """Add individual entities.
        """
        self.add_list(entities)
    
    def add_list(self, entities):
        """Add a sequence of entities.
        """
        for entity in entities:
            if entity in self.entity_branch:
                del self.entity_branch[entity].entities[entity]
                for c in self.collisions.keys():
                    if entity in c:
                        del self.collisions[c]
            self._add_internal(entity)
    
    def remove(self, *entities):
        """Remove individual entities.
        """
        self.remove_list(entities)
    
    def remove_list(self, entities):
        """Remove a sequence of entities.
        """
        for entity in entities:
            entity_branch = self.root.entity_branch
            branch = entity_branch.get(entity)
            if branch:
                del branch.entities[entity]
                del entity_branch[entity]
            
            collisions = self.collisions
            for c in collisions.keys():
                if entity in c:
                    del self.collisions[c]
    
    def entities_in(self, rect):
        """Return list of entities that collide with rect.
        """
        results = []
        self._get_entities_recursive(rect, results)
        return results
    
    def branch_of(self, entity):
        """Return the branch that contains entity. None is returned if entity is
        not in the quadtree.
        """
        return self.entity_branch.get(entity, None)
    
    def level_of(self, entity):
        """Return the level the entity is on. None is returned if entity is not
        in the quadtree.
        """
        branch = self.branch_of(entity)
        if branch:
            return branch.level
        else:
            return None
    
    def collided(self, left, right):
        """This can be called externally, but usually not necessary. The
        quadtree automatically registers collisions as objects are added. This
        can be used on objects that are not currently in the quadtree. Note that
        each call to this method increments coll_tests.
        """
        self.coll_tests += 1
        if left is right:
            return False
        return self._collided(left, right)
    
    def _collided_full(self, left, right):
        """Internal use. _collided will be set to this method if collide_rects
        and collide_entities are both True.
        """
        return self._collided_rects(left, right) and \
            self._collided_entities(left, right, True)
    
    def _collided_rects(self, left, right):
        """Internal use. _collided will be set to this method if collide_rects
        is True and collide_entities is False.
        """
        return left.rect.colliderect(right.rect)
    
    def _collided_entities(self, left, right, rect_tested=False):
        """Internal use. _collided will be set to this method if collide_rects
        is False and collide_entities is True.
        """
        return left.collided(left, right, rect_tested)
    
    def __zero__(self):
        return len(self) == 0
    
    def __iter__(self):
        return iter(self.entity_branch.keys())
    
    def __len__(self):
        return len(self.entity_branch.keys())
