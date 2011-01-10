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
"""

import math
from random import randrange

import pygame
from pygame.locals import *


class QuadTreeNode(object):
    
    def __init__(self, parent, rect, branch_id=1):
        self.root = parent.root
        self.parent = parent
        self.level = parent.level + 1
        self.rect = pygame.Rect(rect)
        self.branch_id = branch_id
        self.branches = []
        self.entities = {}
        self.root.num_levels = max(self.level, self.root.num_levels)
        self._split()
    
    def _split(self):
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
        
        if self.level == 1 and self.root.worst_case > 0:
            ## 9x9 catch-all for worst performance cases that would tend to load
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
        self.root.branch_visits_add += 1
        collided = self.root.collided
        collisions = self.root.collisions
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
    
    def _keep(self, entity):
        self.root.entity_branch[entity] = self
        self.entities[entity] = 1
    
    def test_collisions(self, entity):
        collided = self.root.collided
        collisions = self.root.collisions
        for other in self.entities:
            if collided(other, entity):
                collisions[other,entity] = 1
                collisions[entity,other] = 1
        for b in self.branches:
            b.test_collisions(entity)
    
    def _get_entities_recursive(self, rect, results):
        if self.rect.colliderect(rect):
            results.extend([e for e in self.entities if e.rect.colliderect(rect)])
            for b in self.branches:
                b._get_entities_recursive(rect, results)
    
    @property
    def path(self):
        this_branch = str(self.level) + ':' + str(self.branch_id)
        if self.is_root:
            return this_branch
        else:
            return '_'.join((self.parent.path, this_branch))
    
    def entities_per(self, results):
        this_branch = (self.level, self.branch_id, len(self.entities))
        results.append(this_branch)
        for b in self.branches:
            b.entities_per(results)
        return results
    
    @property
    def is_root(self):
        return self is self.root
    
    @property
    def is_leaf(self):
        return len(self.branches) == 0


class QuadTree(QuadTreeNode):
    
    def __init__(self, rect, min_size=(128,128), worst_case=0, *entities):
        self.root = self
        self.min_size = min_size
        self.worst_case = worst_case
        self.level = 0
        self.entity_branch = {}
        self.collisions = {}
        self.num_levels = 1
        
        self.coll_tests = 0
        self.branch_visits_add = 0
        
        super(QuadTree, self).__init__(self, rect)
        self.add(*entities)
    
    def reset_counters(self):
        self.coll_tests = 0
        self.branch_visits_add = 0
    
    def add(self, *entities):
        for entity in entities:
            if entity in self.entity_branch:
                del self.entity_branch[entity].entities[entity]
                for c in self.collisions.keys():
                    if entity in c:
                        del self.collisions[c]
            self._add_internal(entity)
    
    def remove(self, *entities):
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
        results = []
        self._get_entities_recursive(rect, results)
        return results
    
    def branch_of(self, entity):
        return self.entity_branch.get(entity, None)
    
    def level_of(self, entity):
        branch = self.branch_of(entity)
        if branch:
            return branch.level
        else:
            return None
    
    def collided(self, left, right):
        """Override this to change collision test.
        """
        self.coll_tests += 1
        if left is right:
            return False
        else:
            return left.rect.colliderect(right.rect)
    
    def __zero__(self):
        return len(self) == 0
    
    def __iter__(self):
        return iter(self.entity_branch.keys())
    
    def __len__(self):
        return len(self.entity_branch.keys())
