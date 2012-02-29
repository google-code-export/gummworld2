import sys
from random import randrange, choice
import cProfile
import pstats

import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import State, Engine, Vec2d, HUD, Statf, SubPixelSurface
from gummworld2 import context, model, geometry, spatialhash


class GeomBehavior(object):
    """Superclass providing movement, behavior, and drawing common to all
    entities.
    """
    
    size = 11,11
    
    def __init__(self):
        choices = [-0.5,-0.3,-0.1,0.1,0.3,0.5]
        self.step = Vec2d(choice(choices), choice(choices))
        self.hit = 0
    
    def update(self, *args):
        self.move()
        if self.hit:
            self.hit = 0
            self.image = self.image_red
        else:
            self.image = self.image_green
    
    def move(self):
        sr = self.rect
        wr = State.world.rect
        step = self.step
        self.position += step
        if not wr.contains(sr):
            if sr.x < wr.x or sr.right > wr.right:
                self.position -= (step.x,0)
                step.x = -step.x
            if sr.y < wr.y or sr.bottom > wr.bottom:
                self.position -= (0,step.y)
                step.y = -step.y


class RectGeom(geometry.RectGeometry, GeomBehavior):
    """A rect with graphics, movement, collision detection, and behavior.
    """
    def __init__(self, position):
        geometry.RectGeometry.__init__(self, 0,0,*self.size)
        GeomBehavior.__init__(self)
        
        self.image_green = pygame.surface.Surface(self.rect.size)
        self.image_green.fill(Color('green'))
    
        self.image_red = pygame.surface.Surface(self.rect.size)
        self.image_red.fill(Color('red'))
        
        self.image = self.image_green
        
        self.position = position


class CircleGeom(geometry.CircleGeometry, GeomBehavior):
    """A circle with graphics, movement, collision detection, and behavior.
    """
    def __init__(self, position):
        geometry.CircleGeometry.__init__(self, (0,0), self.size[0]//2)
        GeomBehavior.__init__(self)
        
        self.image_green = pygame.surface.Surface(self.rect.size)
        rect = self.image_green.get_rect()
        self.image_green.fill(Color('black'))
        self.image_green.set_colorkey(Color('black'))
        pygame.draw.circle(self.image_green, Color('green'), rect.center, self.radius)
        
        self.image_red = pygame.surface.Surface(self.rect.size)
        self.image_red.fill(Color('black'))
        self.image_red.set_colorkey(Color('black'))
        pygame.draw.circle(self.image_red, Color('red'), rect.center, self.radius)
        
        self.image = self.image_green
        
        self.position = position
    

class TriangleGeom(geometry.PolyGeometry, GeomBehavior):
    """A triangle with graphics, movement, collision detection, and behavior.
    """
    shape = (5,0),(10,10),(0,10)
    
    def __init__(self, position):
        geometry.PolyGeometry.__init__(self, self.shape, position)
        GeomBehavior.__init__(self)
        
        self.image_green = pygame.surface.Surface(self.rect.size)
        self.image_green.fill(Color('black'))
        self.image_green.set_colorkey(Color('black'))
        pygame.draw.polygon(self.image_green, Color('green'), self.shape)
        
        self.image_red = pygame.surface.Surface(self.rect.size)
        self.image_red.fill(Color('black'))
        self.image_red.set_colorkey(Color('black'))
        pygame.draw.polygon(self.image_red, Color('red'), self.shape)
        
        self.image = self.image_green


class App(Engine):
    
    def __init__(self):

        self.tile_size = 60,60
        self.map_size = 10,10
        self.cell_size = self.map_size[0] * self.tile_size[0]
        self.worst_case = 0
        self.num_sprites = 640
        
        Engine.__init__(self,
            caption='24 SpatialHash Stress Test - [+/-]: Cells | G: Grid',
            resolution=(600,600),
            tile_size=self.tile_size, map_size=self.map_size,
            update_speed=30, frame_speed=0,
        )
        State.camera.init_position((300,300))
        
        # Make starting set of things.
        self.things = []
        world_rect = State.world.rect
        sprites_per_axis = int(self.num_sprites ** 0.5)
        sizex,sizey = world_rect.w/sprites_per_axis, world_rect.h/sprites_per_axis
        for x in xrange(sprites_per_axis):
            for y in xrange(sprites_per_axis):
                self.things.append(self.make_thing((x*sizex+5,y*sizey+5)))
        self.mouse_thing = RectGeom((300,300))
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
        State.world = self.world = spatialhash.SpatialHash(State.map.rect, self.cell_size)
        print State.world
        for thing in self.things:
            State.world.add(thing)
    
    def make_hud(self):
        State.hud = HUD()
        next_pos = State.hud.next_pos
        
        # Frames per second.
        State.hud.add('FPS', Statf(next_pos(),
            'FPS %d', callback=lambda:State.clock.fps, interval=.2))
        
        # Entities on screen.
        State.hud.add('Things', Statf(next_pos(),
            'Things %d', callback=lambda:len(State.world)))
        
        # Cell size.
        State.hud.add('Cell size', Statf(next_pos(),
            'Cell size %d', callback=lambda:self.cell_size))
        
        # Collision tests per tick / Node visits per tick.
        State.hud.add('Collisions', Statf(next_pos(),
            'Collisions %s',
            callback=lambda:'%0.1fK / %dK' % (
                State.world.coll_tests/1000.,
                len(State.world)**2/1000,
            ),
            interval=.25))

    def update(self, dt):
        self.update_world()
        self.update_collisions()
        State.hud.update(dt)
    
    def update_world(self):
        world = State.world
        add = world.add
        for thing in world.objects:
            thing.update()
            # When a thing moves we need to re-add it to the spatial hash.
            add(thing)
    
    def update_collisions(self):
        for c in State.world.collidealllist():
            c[0].hit = True
    
    def draw(self, dt):
        State.screen.clear()
        self.draw_world()
        self.draw_grid()
        State.hud.draw()
        State.screen.flip()
    
    def draw_world(self):
        camera = State.camera
        blit = camera.surface.blit
        for thing in State.world.objects:
            blit(thing.image, thing.rect)
    
    def draw_grid(self):
        if not self.show_grid:
            return
        if self.cell_size == max(*State.world.rect.size):
            return
        world = State.world
        wr = world.rect
        draw_line = pygame.draw.line
        surf = State.camera.view.surface
        color = Color('darkgrey')
        left,right,top,bottom = wr.left,wr.right,wr.top,wr.bottom
        minx = -1
        miny = -1
        for cell_id,cell in enumerate(world.itercells()):
            x,y = world.get_cell_pos(cell_id)
            if x > minx:
                minx = x
                p1 = x,top
                p2 = x,bottom
                draw_line(surf, color, p1, p2)
            if y > miny:
                miny = y
                p1 = left,y
                p2 = right,y
                draw_line(surf, color, p1, p2)
    
    def on_key_down(self, unicode, key, mod):
        if key == K_g:
            # Toggle grid.
            self.show_grid = not self.show_grid
        elif key == K_ESCAPE:
            context.pop()
        elif key in (K_PLUS,K_EQUALS):
            # Resize world using smaller cell size. Minimum size is
            # max(*Thing.size).
            cell_size = self.cell_size * 3/4
            if cell_size < max(*GeomBehavior.size):
                cell_size = max(*GeomBehavior.size)
            self.cell_size = cell_size
            self.make_space()
            for thing in self.things:
                State.world.add(thing)
        elif key == K_MINUS:
            # Resize world using larger cell size. Maximum size is
            # max(*State.world.rect.size).
            cell_size = self.cell_size * 4/3
            if cell_size > max(*State.world.rect.size):
                cell_size = max(*State.world.rect.size)
            self.cell_size = cell_size
            self.make_space()
            for thing in self.things:
                State.world.add(thing)

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
