#!/usr/bin/env python

from random import randrange

import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import State, SpatialHash, HUD, Statf, Vec2d
from gummworld2.geometry import LineGeometry, RectGeometry, CircleGeometry, PolyGeometry


class App(gummworld2.Engine):
    
    def __init__(self):
        
        self.resolution = Vec2d(800,600)
        camera_view_rect = pygame.Rect((0,0), self.resolution)
        camera_target = gummworld2.model.Object(self.resolution/2)
        
        gummworld2.Engine.__init__(self,
            caption='SpatialHash Lines - Space: Rect Cursor',
            resolution=self.resolution,
            camera_target=camera_target,
            camera_view_rect=camera_view_rect,
            update_speed=30, frame_speed=0)
        
        State.camera.init_position(self.resolution/2)
        
        # Spatial hash for collision detection.
        cell_size = 40
        self.world = SpatialHash(self.camera.view.rect, cell_size)
        
        # Make line objects that can be drawn. Stick them in a spatial hash to
        # test collision with the mouse cursor.
        width,height = self.world.rect.size
        for i in xrange(300):
            x1 = randrange(width)
            y1 = randrange(height)
            x2 = randrange(width)
            y2 = randrange(height)
            line = gummworld2.geometry.LineGeometry(x1, y1, x2, y2)
            line.color = Color('darkgreen')
            line.blend = 1
            self.collision_color = Color('red')
            self.world.add(line)
        self.num_objects = len(self.world.objects)
        
        # Make some cursor shapes.
        self.cursor_color = Color('green')
        self.cursor_line = gummworld2.geometry.LineGeometry(0, 0, 0, 30)
        self.cursor_rect = gummworld2.geometry.RectGeometry(0, 0, 30, 30)
        self.cursor_circle = gummworld2.geometry.CircleGeometry((0,0), 15)
        self.cursor_poly = gummworld2.geometry.PolyGeometry(
            ((0,0),(30,0),(30,30),(0,30)))
        self.cursor = self.cursor_rect
        
        pygame.mouse.set_visible(0)
        
        # Make a HUD.
        State.hud = HUD()
        State.hud.set_visible(True)
        next_pos = State.hud.next_pos
        # Frames per second.
        State.hud.add('FPS', Statf(next_pos(),
            'FPS %d', callback=lambda:State.clock.fps, interval=.2))
        # Line count.
        State.hud.add('Lines', Statf(next_pos(),
            'Lines %d', callback=lambda:self.num_objects, interval=2))
    
    def update(self, dt):
        self.collisions = self.world.collide(self.cursor)
        State.hud.update(dt)
    
    def draw(self, interp):
        screen = State.screen
        surface = screen.surface
        draw_line = pygame.draw.line
        collisions = self.collisions
        screen.clear()
        for obj in self.world.objects:
            try:
                surface.blit(obj.image, obj.rect)
            except AttributeError:
                if obj in collisions:
                    color = self.collision_color
                else:
                    color = obj.color
                draw_line(surface, color, obj.p1, obj.p2, obj.blend)
        self.draw_cursor(surface)
        State.hud.draw()
        screen.flip()
    
    def draw_cursor(self, surface):
        draw = pygame.draw
        cursor = self.cursor
        color = self.cursor_color
        if isinstance(self.cursor, LineGeometry):
            draw.aaline(surface, color, cursor.p1, cursor.p2, 1)
        elif isinstance(self.cursor, RectGeometry):
            draw.rect(surface, color, self.cursor.rect, 1)
        elif isinstance(self.cursor, CircleGeometry):
            draw.circle(surface, color, cursor.origin, cursor.radius, 1)
        elif isinstance(self.cursor, PolyGeometry):
            draw.polygon(surface, color, cursor.points, 1)
    
    def on_key_down(self, unicode, key, mod):
        if key == K_ESCAPE:
            self.pop()
        elif key == K_SPACE:
            if isinstance(self.cursor, gummworld2.geometry.LineGeometry):
                self.cursor = self.cursor_rect
                pygame.display.set_caption('SpatialHash Lines - Space: Rect Cursor')
            elif isinstance(self.cursor, gummworld2.geometry.RectGeometry):
                self.cursor = self.cursor_circle
                pygame.display.set_caption('SpatialHash Lines - Space: Circle Cursor')
            elif isinstance(self.cursor, gummworld2.geometry.CircleGeometry):
                self.cursor = self.cursor_poly
                pygame.display.set_caption('SpatialHash Lines - Space: Poly Cursor')
            elif isinstance(self.cursor, gummworld2.geometry.PolyGeometry):
                self.cursor = self.cursor_line
                pygame.display.set_caption('SpatialHash Lines - Space: Line Cursor')
            self.cursor.position = pygame.mouse.get_pos()
    
    def on_mouse_button_down(self, pos, button):
        pass
    
    def on_mouse_button_up(self, pos, button):
        pass
    
    def on_mouse_motion(self, pos, rel, buttons):
        self.cursor.position = pos
    
    def on_quit(self):
        self.pop()


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
