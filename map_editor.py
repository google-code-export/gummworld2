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


__version__ = '0.1'
__vernum__ = (0,1)


"""map_editor.py - A map editor for Gummworld2.
"""


import os
import sys

import pygame
from pygame.locals import Color
import pymunk

progname = sys.argv[0]
progdir = os.path.dirname(progname)
sys.path.append(os.path.join(progdir,'gamelib'))

from gamelib import *


class MapEditor(object):

    def __init__(self, size):
        State.screen = view.Screen(size)
       
        State.map = Map((128,128),(10,10))
        State.world = model.World(State.map.rect)
        self.make_tiles()
       
        State.camera = Camera(State.world.avatar,
            State.screen.surface, State.screen.surface.get_rect())
       
        State.show_labels = True
        State.show_grid = True
        State.show_hud = True

        State.graphics = Graphics()
        State.events = EditorEvents()
        State.clock = GameClock(60,60)
       
        self.make_hud()
       
    def run(self):
        State.running = True
        while State.running:
            State.world.step()
            if State.clock.update_ready():
                self.update()
            if State.clock.frame_ready():
                self.draw()

    def update(self):
        State.events.get()
        State.camera.update()
        if State.show_hud:
            State.hud.update()
   
    def draw(self):
        State.screen.clear()
#        State.canvas.clear()
#        State.graphics.draw_bounding_box(State.canvas.surface, State.world.bounding_box)
#        State.canvas.draw()
        self.draw_tiles()
        self.draw_labels()
        self.draw_grid()
        if State.show_hud:
            State.hud.draw(State.screen.surface)
        State.screen.flip()

    def draw_tiles(self):
        draw = State.camera.draw
        for s in State.camera.visible_tiles:
            draw(s)

    def draw_labels(self):
        """Draw visible labels if enabled.
        """
        if State.show_labels:
            x1,y1,x2,y2 = State.camera.visible_tile_range
            draw_sprite = State.camera.draw
            get_at = State.map.get_label_at
            for x in range(x1,x2):
                for y in range(y1,y2):
                    s = get_at(x,y)
                    draw_sprite(s)

    def draw_grid(self):
        """Draw grid if enabled.
        """
        if State.show_grid:
            x1,y1,x2,y2 = State.camera.visible_tile_range
            SpriteClass = pygame.sprite.Sprite
            draw = State.camera.draw
            grid = State.map.outline
            rect = grid.rect
            for s in State.map.get_tiles(x1, y1, x2, y2):
                if isinstance(s, SpriteClass):
                    rect.topleft = s.rect.topleft
                    draw(grid)

    def make_tiles(self):
        """Create map of tiles.
        """
        # Tiles are sprites; each sprite must have a name, an image, and a rect.
        tw,th = State.tile_size
        mw,mh = State.map_size
        for x in range(mw):
            for y in range(mh):
                s = pygame.sprite.Sprite()
                s.name = (x,y)
                s.image = pygame.surface.Surface((tw,th))
                facx = max(float(x) / mw, 0.01)
                facy = max(float(y) / mh, 0.01)
                s.image.fill((255-255*facx,0,255*facy))
                s.rect = s.image.get_rect(topleft=(x*tw,y*th))
                State.map.add(s)

    def make_hud(self):
        screen_rect = State.screen.rect
        top = 5
        height = ui.hud_font.get_height()
        y = lambda n: top+height*n
        x = screen_rect.x + 5
        State.hud = HUD()
       
        i = 0
        State.hud.add('FPS',
            Statf((x,y(i)), 'FPS %d', callback=State.clock.get_fps))
       
        i += 1
        def get_world_pos(): p = State.camera.position; return int(p.x),int(p.y)
        State.hud.add('WORLD_POS',
            Statf((x,y(i)), 'World %s', callback=get_world_pos, interval=100))
       
        i += 1
        def get_camera_pos():
            x,y = State.camera.rect.center
            return int(x),int(y)
        State.hud.add('CAMERA_POS',
            Statf((x,y(i)), 'Camera %s', callback=get_camera_pos, interval=100))
       
        i += 1
        bb = State.world.bounding_box
        l,b,r,t = bb.left,bb.bottom,bb.right,bb.top
        State.hud.add('WORLD_BOUNDS',
            Stat((x,y(i)), 'Bounds %s'%((int(l),int(b),int(r),int(t),),)))


if __name__ == '__main__':
    map_editor = MapEditor((600,600))
    map_editor.run()
