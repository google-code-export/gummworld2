from math import ceil
import os
import sys
from random import randrange, choice as randchoice
import cProfile
import pstats

import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import State, Engine, Vec2d, HUD, Statf
from gummworld2 import context, model, spatialhash


class Thing(model.Object):
    
    size = 11,11
    
    def __init__(self, position):
        model.Object.__init__(self)
        
        self.rect = pygame.Rect(0,0,*self.size)
        
        self.image_green = pygame.surface.Surface(self.rect.size)
        self.image_green.fill(Color('green'))
        self.image_red = pygame.surface.Surface(self.rect.size)
        self.image_red.fill(Color('red'))
        self.image = self.image_green
        
        self.position = position
        choices = [-0.5,-0.4,-0.3,0.3,0.4,0.5]
        self.step = Vec2d(randchoice(choices), randchoice(choices))
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
            self.image = self.image_red
        else:
            self.image = self.image_green
        self.hit = False
    
    def move(self):
        self.position += self.step
        sr = self.rect
        wr = State.world.rect
        if not wr.contains(sr):
            if sr.x < wr.x or sr.right > wr.right:
                self.position -= (self.step.x,0)
                self.step.x = -self.step.x
            if sr.y < wr.y or sr.bottom > wr.bottom:
                self.position -= (0,self.step.y)
                self.step.y = -self.step.y


class App(Engine):
    
    def __init__(self):
        
        self.resolution = 600,600
        self.tile_size = 60,60
        self.map_size = 10,10
        self.num_cells = 1
        self.num_sprites = 50
        self.add_sprites = 10
        
        self.tune_target_fps = 30
        self.tune_fps_history = []
        self.tune_num_cells = self.num_cells
        self.tune_count = 0
        self.tune_running = True
        self.tune_history = ''
        
        Engine.__init__(self,
            caption='24 SpatialHash - [+/-]: Cells | Space/Bkspc: Things | G: Grid | Mouse Focus: Filter Rect',
            resolution=self.resolution,
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
                self.things.append(Thing((x*sizex+5,y*sizey+5)))
        #self.mouse_thing = Thing((300,300))
        self.filter = False
        self.filter_rect = Rect(0,0,250,250)
        self.make_space()
        
        self.show_grid = True
        self.things_on_screen = 0,0
        self.draw_level = 2
        
        self.make_hud()
        State.show_hud = True
        
        if self.tune_running:
            self.clock.schedule_interval(self.auto_tune, 1.1)
    
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
        State.hud.add('Num cells', Statf(next_pos(),
            'Num cells %d', callback=lambda:self.num_cells))
        
        # Collision tests per tick / Node visits per tick.
        State.hud.add('Collisions', Statf(next_pos(),
            'Collisions %s',
            callback=lambda:'%0.1fK / %dK' % (
                State.world.coll_tests/1000.,
                len(State.world)**2/1000,
            ),
            interval=.25))
    
    def make_space(self):
        cell_size = calc_cell_size(self.resolution, self.num_cells)
        State.world = self.world = spatialhash.SpatialHash(State.map.rect, cell_size)
        for thing in self.things:
            State.world.add(thing)
    
    def inc_cells(self):
        num_cells = self.num_cells + 1
        cell_size = calc_cell_size(self.resolution, num_cells)
        if cell_size < max(*Thing.size):
            num_cells += 1
        self.num_cells = num_cells
        self.make_space()
    
    def dec_cells(self):
        num_cells = self.num_cells - 1
        if num_cells < 1:
            num_cells = 1
        self.num_cells = num_cells
        self.make_space()
    
    def inc_things(self):
        world_rect = State.world.rect
        sprites_per_axis = int(self.num_sprites ** 0.5)
        sizex,sizey = world_rect.w/sprites_per_axis, world_rect.h/sprites_per_axis
        for n in xrange(self.add_sprites):
            x = randrange(sprites_per_axis)
            y = randrange(sprites_per_axis)
            thing = Thing((x*sizex+5,y*sizey+5))
            self.things.append(thing)
            self.world.add(thing)
    
    def dec_things(self):
        for n in xrange(self.add_sprites):
            thing = randchoice(self.things)
            self.world.remove(thing)
            self.things.remove(thing)
    
    def auto_tune(self, dt):
        prev_fps = 0
        history = self.tune_fps_history
        current_fps = self.clock.fps
        
        if self.tune_count > 6:
            print '\nfinished auto tuning'
            self.num_cells = self.tune_num_cells
            self.dec_things()
            self.make_space()
            self.stop_auto_tune()
        else:
            operation = ''
            if current_fps > self.tune_target_fps:
                operation = '+'
                self.tune_num_cells = self.num_cells
                self.tune_count = 0
                self.inc_things()
            else:
                self.inc_cells()
                operation = '|'
                self.tune_count += 1
            sys.stdout.write(operation)
            self.tune_history += operation
            pygame.display.set_caption('Auto tuning: ' + self.tune_history[-20:])
    
    def stop_auto_tune(self):
        self.tune_running = False
        self.clock.unschedule(self.auto_tune)
        pygame.display.set_caption(self.caption)
    
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
        if self.filter and not self.tune_running:
            filter_rect = self.filter_rect
            filter_rect.center = pygame.mouse.get_pos()
            for o in State.world.intersect_objects(filter_rect):
                o.hit = True
        else:
            # Set which=N for different tests.
            which = 2
            
            if which == 0:
                # List of tuples
                coll = State.world.collidealllist()
                for pair in coll:
                    pair[0].hit = True
            elif which == 1:
                # Dict of lists
                coll = State.world.collidealldict()
                for obj,others_list in coll.items():
                    obj.hit = True
            elif which == 2:
                # Flat List of pairs [0,0,1,1,...]
                coll = State.world.collideallflatlist()
                for i in xrange(0, len(coll), 2):
                    pair = coll[i:i+1]
                    pair[0].hit = True
    
    def draw(self, dt):
        State.screen.clear()
        self.draw_world()
        self.draw_grid()
        self.draw_filter()
        State.screen.flip()
    
    def draw_world(self):
        camera = State.camera
        w2s = camera.world_to_screen
        blit = camera.surface.blit
        for thing in State.world.objects:
            pos = w2s(thing.rect.topleft)
            blit(thing.image, pos)
        State.hud.draw()
    
    def draw_grid(self):
        if not self.show_grid:
            return
        if self.num_cells == 1:
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
    
    def draw_filter(self):
        if self.filter and not self.tune_running:
            surf = State.camera.view.surface
            pygame.draw.rect(surf, (150,0,0), self.filter_rect, 1)
    
    def on_key_down(self, unicode, key, mod):
        if key == K_g:
            # Toggle grid.
            self.show_grid = not self.show_grid
        elif key == K_ESCAPE:
            context.pop()
        elif key in (K_PLUS,K_EQUALS):
            self.inc_cells()
            print State.world
            self.stop_auto_tune()
        elif key == K_MINUS:
            self.dec_cells()
            print State.world
            self.stop_auto_tune()
        elif key == K_SPACE:
            self.inc_things()
        elif key == K_BACKSPACE:
            self.dec_things()
    
    def on_quit(self):
        context.pop()
    
    def on_active_event(self, gain, state):
        if self.tune_running:
            return
        if state != 1:
            return
        if gain == 1:
            print 'filter on'
            self.filter = True
        else:
            print 'filter off'
            self.filter = False


def calc_cell_size(resolution, num_cells):
    return int(ceil(resolution[0] / float(num_cells)))


if __name__ == '__main__':
    
    def run_it():
        gummworld2.run(app)
    app = App()
    
    if True:
        run_it()
    else:
        pfile = '24.prof'
        cProfile.run('run_it()', pfile)
        p = pstats.Stats(pfile)
        p.sort_stats('time').print_stats()
        os.remove(pfile)
