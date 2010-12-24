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


"""camera.py - Camera module for Gummworld2.
"""


import pygame

from state import State
from vec2d import Vec2d


class Camera(object):
  
    def __init__(self, target, surface, rect):
        self.target = target
        self.surface = surface
        self.rect = rect

    def update(self):
        if self.rect.center != self.target.position:
            self.rect.center = self.target.position

    @property
    def position(self):
        return self.target.position
   
    @property
    def screen_position(self):
        return Vec2d(self.world_position) - self.rect.topleft

    def world_to_screen(self, xy):
        cx,cy = self.rect.center
        sx,sy = State.screen.rect.center
        x,y = xy
        return Vec2d(cx-x+sx, cy-y+sy)

    def screen_to_world(self, xy):
        cx,cy = self.rect.center
        sx,sy = State.screen.rect.center
        x,y = xy
        return Vec2d(sx-x+cx, sy-y+cy)

    @property
    def visible_tile_range(self):
        tile_x,tile_y = State.tile_size
        (l,t),(r,b) = self.rect.topleft,self.rect.bottomright
        left = int(round(float(l) / tile_x - 1))
        right = int(round(float(r) / tile_x + 2))
        top = int(round(float(t) / tile_y - 1))
        bottom = int(round(float(b) / tile_y + 2))
        return left,top,right,bottom

    @property
    def visible_tiles(self):
        return State.map.get_tiles(*self.visible_tile_range)

    def draw(self, s):
        if isinstance(s, pygame.sprite.Sprite):
            cr = self.rect
            sr = s.rect
            self.surface.blit(s.image, (sr.x-cr.x, sr.y-cr.y))


if __name__ == '__main__':
    from pygame.locals import *
    from view import Screen
    from map import Map
    
    pygame.init()
    clock = pygame.time.Clock()
    
    # Set up a screen and a subrect for the two types of drawing supported by
    # the camera.
    State.screen = Screen((300,300))
    screen = State.screen.surface
    screen_rect = screen.get_rect()
    subrect = pygame.Rect(25,25,250,200)
    subsurf = screen.subsurface(subrect)
    draw_rect = subrect.copy()

    # Set up the map.
    State.map = Map((128,128), (10,6))
    
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
    
    # Avatar is the camera's target. Camera follows avatar around the map.
    avatar = pygame.sprite.Sprite()
    avatar.position = Vec2d(256,256)
    avatar.position = Vec2d(0,0)
    State.camera = Camera(avatar, screen, screen.get_rect())
    
    # Movement and runtime display options.
    movex,movey = 0,0
    State.show_labels = True
    State.show_grid = True
    
    def handle_events():
        """ Handle events.
        Cursor keys -> move about the map.
        Space -> reset avatar position.
        Tab -> toggle between drawing full window and a subsurface.
        L -> toggle labels.
        G -> toggle grid.
        """
        global movex, movey
        for e in pygame.event.get():
            if e.type == KEYDOWN:
                if e.key == K_RIGHT: movex = 1
                elif e.key == K_LEFT: movex = -1
                elif e.key == K_DOWN: movey = 1
                elif e.key == K_UP: movey = -1
                elif e.key == K_SPACE: avatar.position = Vec2d(0,0)
                elif e.key == K_TAB:
                    if State.camera.surface is screen:
                        State.camera.surface = subsurf
                        State.camera.rect = subrect
                    else:
                        State.camera.surface = screen
                        State.camera.rect = screen_rect
                elif e.key == K_g: State.show_grid = not State.show_grid
                elif e.key == K_l: State.show_labels =  not State.show_labels
            elif e.type == KEYUP:
                if e.key in (K_RIGHT,K_LEFT): movex = 0
                elif e.key in (K_DOWN,K_UP): movey = 0
    
    def draw_tiles():
        """Draw visible tiles.
        """
        draw = State.camera.draw
        for s in State.camera.visible_tiles:
            draw(s)
    
    def draw_labels(x1, y1, x2, y2):
        """Draw visible labels if enabled.
        """
        if State.show_labels:
            draw_sprite = State.camera.draw
            get_at = State.map.get_label_at
            for x in range(x1,x2):
                for y in range(y1,y2):
                    s = get_at(x,y)
                    draw_sprite(s)

    def draw_grid(x1, y1, x2, y2):
        """Draw grid if enabled.
        """
        if State.show_grid:
            SpriteClass = pygame.sprite.Sprite
            draw = State.camera.draw
            grid = State.map.outline
            rect = grid.rect
            for s in State.map.get_tiles(x1, y1, x2, y2):
                if isinstance(s, SpriteClass):
                    rect.topleft = s.rect.topleft
                    draw(grid)

    # Run it.
    while True:
        clock.tick(120)
        State.screen.clear()

        # See handle_events for keypresses that modify state.

        # Draw tiles, labels, and grid.
        draw_tiles()
        x1,y1,x2,y2 = State.camera.visible_tile_range
        draw_labels(x1,y1,x2,y2)
        draw_grid(x1,y1,x2,y2)
        # Draw a cosmetic box around the subsurface.
        if State.camera.surface is subsurf:
            pygame.draw.rect(screen, (99,99,99), draw_rect, 1)
        
        # Update game.
        handle_events()
        if (movex,movey):
            avatar.position += (movex,movey)
            State.camera.update()
        
        State.screen.flip()
