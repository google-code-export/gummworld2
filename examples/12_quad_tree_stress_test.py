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


__doc__ = """quad_tree_stress_test.py - Stress test of quad_tree.py.

THE TECHNOBABBLE

This is a worst-case usage of the quad tree. Worst case is something involving
a large number of entities, all of which need to be updated every tick, and all
drawn in every frame. The quad tree is not very efficient for this, so it forms
a good stress test.

The whole intent of the quad tree is to optimize storing entities in a way that
adding or moving entities, retrieving entities within a bounding rect, and
collision detection maintains reasonably good scalable performance. It does so
by dividing and subdividing a map into sections, such that the number of
collision checks is minimized when activity is confined to a relatively small
area of the map.

In order to accomplish this, the quad tree prefers to store entities at the
lowest level branch in which it can be entirely contained. It dislikes storing
entities in level 1. In fact, storing anything in level 1 is very expensive as
every operation involves all the sprites in level 1.

Contributing to the worst case are sporadic situations like a number of entities
parking on level 2 grid lines or crossing them simultaneously. This boosts the
number of entities forced into level 1, and increases the number of collision
checks required during entity placement (add, aka move).

In addition, there is the situation where entities roam outside the world
bounds. This should not happen in a well written game, but if it does the
entities will be forced into level 1.

These situations can be handled by an extension of the quad tree, which is
enabled by telling the constructor worst_case=SOME_INT. This triggers the
creation of a 9x9 group of auxilliary branches that cover the entire world map,
and are considered before placing entities in level 1. SOME_INT represents the
number of pixels to inflate the 9x9 grid beyond the world bounds. There is
no penalty to making this value very large. However, if these grids are not
needed they do add some overhead to collision detection, and operations that
walk the entire quad tree.


THE DEMO

The sprite's surface alpha indicates the quad tree level in which it's stored.
The higher the alpha, the lower the level. Level 1 is the top level--the worst
level to be in--and displays the brightest. Sprites that have recently collided
will be colored red, and eventually turn green after a short time.

In order to demonstrate the worst of the worst, the demo begins with 100 sprites
and the quad tree's worst-case handling turned off.

Try increasing the number of entities ('+' or '=' key) until frame rate drops
below 50 or 60. Older computers may need to reduce the number of entities with
the '-' key. Once you see the frame rate around 30 to 50, turn on worst-case
handling with the W key to see the difference it can make. Keep an eye on the
Catch-all HUD item, which shows the number of entities in level 1 over the
number of entities in the 9x9 branches. The Worst case HUD item is an "idiot
light" that indicates there are a high number of entities in level 1.

Pick different grid levels to draw and observe the sprite alpha as the shapes
cross grid lines. This will give you an idea of what levels they hit as they
traverse the map.

Controls:

    G will toggle grid display. Pressing 1 through 9 will select the quad tree
    level for which the grid should be drawn. 9 is the catch-all 9x9 level
    impelented to alleviate default selection of level 1 for entities parked on
    level 2 grid lines or slightly outside the world bounds.

    Press W to toggle worst-case handling. Worst case is the 9x9 level.

    Press '+' or '=' to add 20 things to the quad tree, press '-' to remove 20
    things.
"""

import sys
from random import randrange, choice
import cProfile
import pstats

import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import *


class Thing(model.Object):
    
    def __init__(self, position):
        model.Object.__init__(self)
        
        self.rect = pygame.Rect(0,0,20,20)
        
        self.image_green = pygame.surface.Surface(self.rect.size)
        self.image_green.fill(Color('green'))
        self.image_red = pygame.surface.Surface(self.rect.size)
        self.image_red.fill(Color('red'))
        self.image = self.image_green
        
        self.position = position
        choices = [-0.5,-0.3,-0.1,0.1,0.3,0.5]
        self.step = Vec2d(choice(choices), choice(choices))
        self.hit = 0
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        p = self._position
        p.x,p.y = val
        self.rect.center = round(p.x),round(p.y)
    
    def update(self, *args):
        self.move()
        if self.hit:
            self.hit = 0
            self.image = self.image_red
        else:
            self.image = self.image_green
        if len(args) == 2:
            level,num_levels = args
            alpha = int(255-round(float(level)/num_levels*200))
            self.image.set_alpha(alpha)
    
    def move(self):
        wx,wy = self.position + self.step
        rect = State.world.rect
        w,h = Vec2d(self.rect.size) // 2
        wx1 = max(min(wx,rect.right+w), rect.left-w)
        wy1 = max(min(wy,rect.bottom+h), rect.top-h)
        if wx1 != wx:
            self.step.x = -self.step.x
        if wy1 != wy:
            self.step.y = -self.step.y
        self.position = wx1,wy1

    def draw(self):
        camera = State.camera
        pos = camera.world_to_screen(self.rect.topleft)
        camera.surface.blit(self.image, pos)


class App(Engine):
    
    def __init__(self):

        self.tile_size = 60,60
        self.map_size = 10,10
        self.min_size = 128,128
        self.worst_case = 0
        self.num_sprites = 100

        Engine.__init__(self,
            caption='12 Quadtree Stress Test - [-+]: Entities | W: Worst case | [1239]: Level grid',
            resolution=(600,600),
            tile_size=self.tile_size, map_size=self.map_size,
            update_speed=30, frame_speed=0, default_schedules=False,
            world_type=QUADTREE_WORLD,
        )
        State.camera.init_position((300,300))
        
        # Make starting set of things.
        self.things = []
        world_rect = State.world.rect
        sprites_per_axis = self.num_sprites ** 0.5
        x_step = int(round(world_rect.width / sprites_per_axis))
        y_step = int(round(world_rect.height / sprites_per_axis))
        for x in xrange(0, world_rect.width, x_step):
            for y in xrange(0, world_rect.height, y_step):
                self.things.append(Thing((x,y)))
        self.mouse_thing = Thing((300,300))
        self.make_space()
        
        self.show_grid = True
        self.things_on_screen = 0,0
        self.draw_level = 2
        
        self.make_hud()
        State.show_hud = True
    
    def make_space(self):
        world_rect = State.world.rect
        self.world = State.world = model.WorldQuadTree(
            world_rect, min_size=self.min_size, worst_case=self.worst_case)
        State.world.add_list(self.things)
    
    def make_hud(self):
        State.hud = HUD()
        State.clock.schedule_update_priority(State.hud.update, 1.0)
        next_pos = State.hud.next_pos
        
        # Frames per second
        State.hud.add('FPS', Statf(next_pos(),
            'FPS %d', callback=State.clock.get_fps, interval=.2))
        
        # Which level's grid is drawn / Number of levels there are
        def get_levels():
            return str(self.draw_level)+'/'+str(State.world.num_levels)
        State.hud.add('Show/Levels', Statf(next_pos(),
            'Show/Levels %s', callback=get_levels))
        
        # Entities on screen / Total entities
        def get_vis():
            vis,tot = self.things_on_screen
            return str(vis)+'/'+str(tot)
        State.hud.add('Visible/Total', Statf(next_pos(),
            'Visible/Total %s', callback=get_vis))
        
        # Entities in level 1 / Entities in catch-all levels (aka level 9x9)
        def get_catch_all():
            level_1 = len(State.world.entities)
            level_9 = 0
            for b in State.world.branches[4:]:
                level_9 += len(b.entities)
            return '%02d'%level_1 + '/' + '%02d'%level_9
        State.hud.add('Catch-all', Statf(next_pos(),
            'Catch-all %s', callback=get_catch_all, interval=.15))
        
        # Collision tests per tick / Node visits per tick
        def get_collisions():
            colls = '%05d' % State.world.coll_tests
            visits = '%05d' % State.world.branch_visits_add
            return colls+'/'+visits
        State.hud.add('Colls/Visits', Statf(next_pos(),
            'Colls/Visits %s', callback=get_collisions, interval=.15))

        def get_worst_case():
            count = len(State.world.entities)
            if count >= 15:
                if count > self.worst_case_count or self.worst_case_cooldown == 0:
                    self.worst_case_cooldown = 7
                    return '!! %d in level 1' % count
            if self.worst_case_cooldown == 0:
                self.worst_case_count = 0
                return 'OK'
            if self.worst_case_cooldown > 0:
                self.worst_case_cooldown -= 1
            return 'OK'
        self.worst_case_count = 0
        self.worst_case_cooldown = 30
        State.hud.add('Worst case', Statf(next_pos(),
            'Worst case: %s', callback=get_worst_case, interval=.15))

    def update(self, dt):
        self.update_world()
        self.update_collisions()
    
    def update_world(self):
        space = State.world
        space.reset_counters()
        level_of = space.level_of
        num_levels = space.num_levels
        add = space.add
        for thing in space:
            thing.update(level_of(thing), num_levels)
            add(thing)
        things = space.entities_in(State.camera.rect)
        self.things_on_screen = (len(things),len(space))
    
    def update_collisions(self):
        for c in State.world.collisions:
            c[0].hit = 255
    
    def draw(self, dt):
        State.screen.clear()
        self.draw_grid(self.draw_level)
        self.draw_world()
        State.screen.flip()
    
    def draw_world(self):
        things = State.world.entities_in(State.camera.rect)
        for thing in things:
            thing.draw()
        State.hud.draw()
    
    def draw_grid(self, level=0, b=None):
        if not self.show_grid:
            return
        if b is None:
            b = State.world
        if b.level == level or (level == 9 and b.level == 2):
            camera = State.camera
            r = pygame.Rect(b.rect)
            r.topleft = camera.world_to_screen(r.topleft)
            if b.rect.colliderect(State.camera.rect):
                pygame.draw.rect(camera.surface, Color('grey'), r, 1)
        elif level == 9 and b.level == 1:
            for b in b.branches[4:]:
                self.draw_grid(level, b)
        else:
            for b in b.branches[0:4]:
                self.draw_grid(level, b)
    
    def on_key_down(self, unicode, key, mod):
        if key == K_g:
            # Toggle grid.
            self.show_grid = not self.show_grid
        elif key in range(K_0,K_9+1):
            # Set level of grid to show.
            self.draw_level = key - K_0
        elif key == K_ESCAPE:
            context.pop()
        elif key == K_w:
            # Toggle worst-case handling.
            if self.worst_case == 0:
                self.worst_case = 99
            else:
                self.worst_case = 0
            self.make_space()
        elif key in (K_PLUS,K_EQUALS):
            # Add some things.
            new_entities = []
            world_rect = State.world.rect
            for i in range(20):
                x = randrange(world_rect.width)
                y = randrange(world_rect.height)
                new_entities.append(Thing((x,y)))
            self.things.extend(new_entities)
            State.world.add(*new_entities)
        elif key == K_MINUS:
            # Remove some things.
            del_things = self.things[0:20]
            del self.things[0:20]
            State.world.remove(*del_things)

    def on_quit(self):
        context.pop()

    def on_mouse_motion(self, pos, rel, buttons):
        self.mouse_thing.position = State.camera.screen_to_world(pos)
        State.world.add(self.mouse_thing)


if __name__ == '__main__':
    
    def run_it():
        gummworld2.run(app)
    
    app = App()

    if True:
        run_it()
    else:
        cProfile.run('run_it()')
        p = pstats.Stats()
        p.print_stats()
