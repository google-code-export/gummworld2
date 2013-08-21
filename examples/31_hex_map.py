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


__version__ = '$Id: 29_basic_map_renderer.py 392 2013-08-04 05:28:14Z stabbingfinger@gmail.com $'
__author__ = 'Gummbum, (c) 2011-2013'


__doc__ = """31_hex_map.py - An example using an irregular tile with the
BasicMapRenderer in Gummworld2.

Use of irregular tiles usually brings performance problems because the
images need to have transparent parts so they abut properly. Blitting many
transparent images can really bog down the CPU, which yields slower frame
rates and can result in a gameplay experience that is not smooth.

This program demonstrates that the BasicMapRenderer is very well suited to
this use case.
"""


import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import context, geometry, toolkit
from gummworld2 import State, Engine
from gummworld2 import BasicMap, BasicLayer, BasicMapRenderer
from gummworld2.geometry import PolyGeometry
from gummworld2 import Statf, Vec2d


class CameraTarget(object):
    
    def __init__(self, position=(0,0)):
        self._position = Vec2d(position)
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        self._position[:] = val


# Define a few constants.
HEX_WIDTH = 50.0
HEX_HEIGHT = 42.0
HEX_BOUNDS = Rect(0,0,50,50)
HEX_POINTS_FLOAT = HEX_POINTS_INT = None
def __init_hex_points():
    global HEX_WIDTH, HEX_HEIGHT, HEX_BOUNDS, HEX_POINTS_FLOAT, HEX_POINTS_INT
    
    x = y = 0.0
    w = HEX_WIDTH
    h = HEX_HEIGHT
    
    # hex points clockwise...
    topleft = (w*1/4,y+1)
    topright = (w*3/4,y+1)
    centerright = (w-1,h*1/2)
    bottomright = (w*3/4,h-1)
    bottomleft = (w*1/4,h-1)
    centerleft = (x+1,h*1/2)
    
    HEX_POINTS_FLOAT = (
        # clockwise...
        topleft, topright, centerright,
        bottomright, bottomleft, centerleft,
    )
    
    HEX_POINTS_INT = tuple(
        [(int(round(x)),int(round(y))) for x,y in HEX_POINTS_FLOAT]
    )

__init_hex_points()


class HexTile(PolyGeometry):
    
    normal_image = None
    highlight_image = None
    
    def __init__(self, position):
        PolyGeometry.__init__(self, HEX_POINTS_FLOAT, position)
        if self.normal_image is None:
            fill = Color('#cc9966')
            normal = Color('#663300')
            high = Color('gold')
            self.normal_image = self._make_image(fill, normal)
            self.highlight_image = self._make_image(fill, high)
            self.image = self.normal_image
    
    def _make_image(self, fill, outline):
        image = pygame.Surface(self.rect.size)
        image.set_colorkey(Color('black'))
        pygame.draw.polygon(image, fill, HEX_POINTS_INT)
        pygame.draw.polygon(image, outline, HEX_POINTS_INT, 3)
        return image
    
    def normal(self):
        self.image = self.normal_image
    
    def highlight(self):
        self.image = self.highlight_image
    
    def collide_point(self, point):
        return geometry.point_in_poly(point, self.points)


class App(Engine):
    
    def __init__(self):
        
        screen_size = Vec2d(800,600)
        map_size = Vec2d(100,100)
        tile_size = Vec2d([int(i) for i in HEX_BOUNDS])
        world_rect = Rect((0,0), map_size*tile_size)
        
        self.movex = 0
        self.movey = 0
        
        self.map = make_hex_tiles(map_size, label=True)
        Engine.__init__(self,
            resolution=screen_size,
            map = self.map,
            world_type=Engine.SIMPLE_WORLD, world_args={'rect':world_rect},
            camera_target=CameraTarget(screen_size//2),
            frame_speed=0)
        
        self.scroll_speed = 5
        self.mouse_pos = Vec2d(pygame.mouse.get_pos())
        self.hex_pick = None
        
        self.renderer = BasicMapRenderer(
            self.map, max_scroll_speed=self.scroll_speed)
        self.which_renderer = 0
        self.renderers = [
            toolkit.draw_tiles,
            self.renderer.draw_tiles,
        ]
        
        toolkit.make_hud()
        next_pos = State.hud.next_pos
        State.hud.add('BasicMap tiles', Statf(next_pos(),
            'BasicMap tiles %d', callback=self._count_map_tiles, interval=.2))
        State.hud.add('Renderer tiles', Statf(next_pos(),
            'Renderer tiles %d', callback=lambda:len(self.renderer._tiles), interval=.2))
        self.hex_pick_for_hud = (
            lambda:str(self.hex_pick.rect.center) if self.hex_pick else 'None'
        )
        State.hud.add('Hex pick', Statf(next_pos(),
            'Hex pick %s', callback=self.hex_pick_for_hud, interval=.2))
        State.hud.add('Using renderer', Statf(next_pos(),
            'Using renderer %s',
            callback=lambda:True if self.which_renderer==1 else False,
            interval=.2))
    
    def _count_map_tiles(self):
        basic_map = State.map
        ids = toolkit.get_visible_cell_ids(
            State.camera, basic_map, self.scroll_speed)
        layers = toolkit.get_objects_in_cell_ids(basic_map, ids)
        count = 0
        for layer in layers:
            count += len(layer)
        return count
    
    def update(self, dt):
        self.mouse_pick()
        if self.movex or self.movey:
            State.camera.position += self.movex,self.movey
        State.camera.update()
        self.renderer.set_rect(center=State.camera.rect.center)
        State.hud.update(dt)
    
    def draw(self, interp):
        screen = State.screen
        screen.clear()
        self.renderers[self.which_renderer]()
        self.draw_hex_pick()
        State.hud.draw()
        screen.flip()
    
    def draw_hex_pick(self):
        hex = self.hex_pick
        if hex:
            pos = State.camera.world_to_screen(hex.rect.topleft)
            State.screen.blit(hex.image, pos)
    
    def on_mouse_motion(self, pos, rel, buttons):
        self.mouse_pos[:] = pos
        self.mouse_pick()
    
    def mouse_pick(self):
        worldx,worldy = world_pos = State.camera.screen_to_world(self.mouse_pos)
        space = self.map.layers[0].objects
        cell_id = space.index_at(worldx, worldy)
        if cell_id is None:
            self._clear_pick()
            return
        cell = space.get_cell(cell_id)
        for obj in cell:
            if obj.collide_point(world_pos):
                self._clear_pick()
                self._set_pick(obj)
    
    def _set_pick(self, obj):
        obj.highlight()
        self.renderer.set_dirty(obj.rect)
        self.hex_pick = obj
        self.hex_pick.position = obj.position
    
    def _clear_pick(self):
        if self.hex_pick:
            self.hex_pick.normal()
            self.renderer.set_dirty(self.hex_pick.rect)
            self.hex_pick = None
    
    def on_key_down(self, unicode, key, mod):
        if key == K_DOWN: self.movey += self.scroll_speed
        elif key == K_UP: self.movey += -self.scroll_speed
        elif key == K_RIGHT: self.movex += self.scroll_speed
        elif key == K_LEFT: self.movex += -self.scroll_speed
        elif key == K_SPACE:
            self.which_renderer = 0 if self.which_renderer else 1
        elif key == K_ESCAPE: context.pop()
    
    def on_key_up(self, key, mod):
        if key == K_DOWN: self.movey -= self.scroll_speed
        elif key == K_UP: self.movey -= -self.scroll_speed
        elif key == K_RIGHT: self.movex -= self.scroll_speed
        elif key == K_LEFT: self.movex -= -self.scroll_speed
    
    def on_quit(self):
        context.pop()


def make_hex_tiles(map_size, label=True):
    w,h = map_size
    hexmap = BasicMap(w, h, HEX_WIDTH, HEX_HEIGHT)
    layer = BasicLayer(hexmap, 0)
    hexmap.layers.append(layer)
    
    iround = lambda x: int(round(x))
    xstart = iround(HEX_WIDTH/2)
    xend = iround(hexmap.pixel_width)
    xstep = iround(HEX_WIDTH+HEX_WIDTH*1/2+1)
    ystart = iround(HEX_HEIGHT/2)
    yend = iround(hexmap.pixel_height)
    ystep = iround(HEX_HEIGHT*1/2)
    shift = True
    for y in xrange(ystart, yend, ystep):
        shift = not shift
        shift_val = HEX_WIDTH*3/4 if shift else 0
        for x in xrange(xstart, xend, xstep):
            x += shift_val
            hextile = HexTile((x,y))
            layer.add(hextile)
    
    return hexmap


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
