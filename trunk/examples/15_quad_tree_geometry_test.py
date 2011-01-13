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

See the 12_quad_tree_stress_test.py doc for the basic quad tree explanation.

This is another worst-case usage of the quad tree. It differs from
12_quad_tree_stress_test.py in that it adds collision detection of geometry. It
is not a rect-vs-rect approximation; it is fairly precise circle-vs-triangle,
circle-vs-rect, etc. This level of testing is quite a bit more work for the
computer, so typically one would want the quad tree to perform a rect-vs-rect
test to detect proximity (because it is a comparatively fast test), and then
perform a shape-vs-shape test if the entities are in proximity.

One needs to direct the quad tree to do this more elaborate testing. Whether
using the Engine class or QuadTree classes, pass the constructor these
arguments:
    
    collide_rects=True, collide_entities=True

This turns on rect-vs-rect testing and shape-vs-shape testing, respectively.

In order to use shape-vs-shape testing, one's entities also need to have the
required attributes:
    
    *   Shape essentials, e.g. a circle requires the origin and radius
        attributes.
    *   A collided attribute, which is one of the *_collided_other static-
        method functions from the geometry module.

See the documentation for circle_collided_other() for details regarding the
shape attributes and collided method.

It is probably best to implement the shape attributes as properties, as they
hold the shape and the rect holds the position. See TriangleGeom.points in this
demo for an example.


THE DEMO

The sprite's surface alpha indicates the quad tree level in which it's stored.
The higher the alpha, the lower the level. Level 1 is the top level--the worst
level to be in--and displays the brightest. Sprites that have recently collided
will be colored red, and eventually turn green after a short time.

In order to demonstrate the worst of the worst, the demo begins with a number of
sprites and the quad tree's worst-case handling turned off.

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

    Press '+' or '=' to add 10 things to the quad tree, press '-' to remove 10
    things.
"""

import sys
from random import randrange, choice
import cProfile
import pstats

import pygame
from pygame.locals import *

import paths
from gamelib import *


class RectGeom(model.Object):
    
    def __init__(self, position):
        super(RectGeom, self).__init__()
        
        self.rect = pygame.Rect(0,0,25,25)
        
        self.image_green = pygame.surface.Surface(self.rect.size)
        self.image_green.fill(Color('green'))
        self.image_red = pygame.surface.Surface(self.rect.size)
        self.image_red.fill(Color('red'))
        self.image = self.image_green
        
        self.position = position
        choices = [-0.5,-0.3,-0.1,0.1,0.3,0.5]
        self.step = Vec2d(choice(choices), choice(choices))
        self.hit = 0
    
    ## entity's collided, static method used by QuadTree callback
    collided = staticmethod(geometry.rect_collided_other)
    
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


class CircleGeom(RectGeom):
    def __init__(self, position):
        super(CircleGeom, self).__init__(position)
        
        self.rect = self.image.get_rect(topleft=(0,0))
        self.image_green.fill(Color('black'))
        self.image_green.set_colorkey(Color('black'))
        pygame.draw.circle(self.image_green, Color('green'), self.origin, self.radius)
        
        self.image_red.fill(Color('black'))
        self.image_red.set_colorkey(Color('black'))
        pygame.draw.circle(self.image_red, Color('red'), self.origin, self.radius)
        
        self.position = position
    
    ## entity's collided, static method used by QuadTree callback
    collided = staticmethod(geometry.circle_collided_other)
    
    ## properties for circle, required by circle_collided_other
    @property
    def origin(self):
        return self.rect.center
    @origin.setter
    def origin(self, val):
        self.position = val
    @property
    def radius(self):
        return self.rect.width // 2


class TriangleGeom(RectGeom):
    def __init__(self, position):
        super(TriangleGeom, self).__init__(position)
        
        self.rect = self.image.get_rect(topleft=(0,0))
        r = self.rect
        self._points = [
            (r.centerx,r.top),
            r.bottomright,
            r.bottomleft,
        ]
        
        self.image_green.fill(Color('black'))
        self.image_green.set_colorkey(Color('black'))
        pygame.draw.polygon(self.image_green, Color('green'), self.points)
        
        self.image_red.fill(Color('black'))
        self.image_red.set_colorkey(Color('black'))
        pygame.draw.polygon(self.image_red, Color('red'), self.points)
        
        self.position = position
    
    ## entity's collided, static method used by QuadTree callback
    collided = staticmethod(geometry.poly_collided_other)
    
    ## properties for circle, required by circle_collided_other
    @property
    def points(self):
        l,t = self.rect.topleft
        return [(x+l,y+t) for x,y in self._points]


class App(Engine):
    
    def __init__(self):

        # world: 2560x2560, 256 entities
        #   (128,128), (20,20), (256,256)
        #   (128,128), (20,20), (256,256)
        # world: 1280x1280, 256 entities
        #   (128,128), (10,10), (256,256)
        #   (128,128), (10,10), (256,256)
        # world: 600x600, 256 entities
        #   (60,60),   (10,10), (128,128)
        #   (60,60),   (10,10), (128,128)
        self.tile_size = 60,60
        self.map_size = 10,10
        self.min_size = 128,128
        self.worst_case = 0
        self.num_sprites = 90

        super(App, self).__init__(
            resolution=(600,600),
            tile_size=self.tile_size, map_size=self.map_size,
            update_speed=30, frame_speed=0,
        )
        State.camera.position = 300,300

        # Make starting set of things.
        self.things = []
        world_rect = State.world.rect
        for i in xrange(self.num_sprites):
            x = randrange(world_rect.width)
            y = randrange(world_rect.height)
            ## make a variety of things
            thing = self.make_thing((x,y))
            self.things.append(thing)
        self.mouse_thing = RectGeom((300,300))
        self.mouse_thing.step = Vec2d(0,0)
        self.make_space()
        
        self.show_grid = True
        self.things_on_screen = 0,0
        self.draw_level = 2
        
        self.make_hud()
        State.show_hud = True
    
    def make_thing(self, pos):
        GeomClass = choice([
            RectGeom,
            CircleGeom,
            TriangleGeom,
        ])
        return GeomClass(pos)
    
    def make_space(self):
        world_rect = State.world.rect
        State.world = model.WorldQuadTree(
            world_rect, min_size=self.min_size, worst_case=self.worst_case,
            ## turn on both rect.colliderect and entity.collided tests
            collide_rects=True,
            collide_entities=True)
        State.world.add(*self.things)
    
    def make_hud(self):
        State.hud = HUD()
        next_pos = State.hud.next_pos
        
        # Frames per second
        State.hud.add('FPS', Statf(next_pos(),
            'FPS %d', callback=State.clock.get_fps))
        
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
            'Catch-all %s', callback=get_catch_all, interval=66))
        
        # Collision tests per tick / Node visits per tick
        def get_collisions():
            colls = '%05d' % State.world.coll_tests
            visits = '%05d' % State.world.branch_visits_add
            return colls+'/'+visits
        State.hud.add('Colls/Visits', Statf(next_pos(),
            'Colls/Visits %s', callback=get_collisions, interval=66))

        def get_worst_case():
            alert_threshold = 15
            count = len(State.world.entities)
            if count >= alert_threshold:
                if count > self.worst_case_count or self.worst_case_cooldown == 0:
                    self.worst_case_cooldown = 30
                    return '!! %d in level 1' % count
            if self.worst_case_cooldown == 0:
                self.worst_case_count = 0
                return 'OK'
            if self.worst_case_cooldown > 0:
                self.worst_case_cooldown -= 1
            return None
        self.worst_case_count = 0
        self.worst_case_cooldown = 30
        State.hud.add('Worst case', Statf(next_pos(),
            'Worst case: %s', value='OK', callback=get_worst_case, interval=66))

    def update(self):
        self.update_world()
        self.update_collisions()
        State.hud.update()
    
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
    
    def draw(self):
        State.screen.clear()
        if self.show_grid:
            self.draw_grid(self.draw_level)
        self.draw_world()
        State.screen.flip()
    
    def draw_world(self):
        things = State.world.entities_in(State.camera.rect)
        for thing in things:
            thing.draw()
        State.hud.draw()
    
    def draw_grid(self, level=0, b=None):
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
            sys.exit()
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
            for i in range(10):
                x = randrange(world_rect.width)
                y = randrange(world_rect.height)
                new_entities.append(self.make_thing((x,y)))
            self.things.extend(new_entities)
            State.world.add(*new_entities)
        elif key == K_MINUS:
            # Remove some things.
            del_things = self.things[0:10]
            del self.things[0:10]
            State.world.remove(*del_things)

    def on_quit(self):
        sys.exit()

    def on_mouse_motion(self, pos, rel, buttons):
        self.mouse_thing.position = State.camera.screen_to_world(pos)
        State.world.add(self.mouse_thing)

app = App()
if True:
    app.run()
else:
    cProfile.run('app.run()')
    p = pstats.Stats()
    p.print_stats()
