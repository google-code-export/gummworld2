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


"""16_reduce_map.py - An example of using toolkit.reduce_map_layers in
Gummworld2.

This demo does not use pymunk.

The results of this demo can be impressive on computers with fast CPUs.

The demo allows one to see the efficiency of different combinations of layer
reduction and collapse.

Maps with many small tiles are great for designing maps with interesting detail.
But they take a lot longer for Python to process than larger tiles because there
are more objects in the working lists. toolkit.collapse_map() can help with
this.

Maps with many layers are great for layer control, map organization, layered
effects, and other possibilities. But it is costly to blit multiple images for
the same map square. If one does the blitting up front and caches the resulting
image, then there is only one image to blit instead of one from several layers.
If layers are not needed for effects, then toolkit.reduce_map_layers() can help
in this way.

When the demo is run, watch the FPS and Layer/Tiles metrics in the HUD while
pressing O for Original map, R for Reduced map, C for Collapsed map, and B for
Both collapsed-and-reduced map.

On a geek note, this demo loads a map that has sparse layers. Which is to say
not every square of every layer has a tile defined for it. This is efficient
map design courtesy of Tiled Map Editor, and has real savings. In our case a
fully populated map would have 2400 tiles to render per frame whereas our map
has only 728 tiles to render. If a program had a fully populated map, then there
would be great efficiency in reducing all layers down to one, or 2400 tiles down
to 400 tiles.
"""


import pygame
from pygame.sprite import Sprite
from pygame.locals import (
    FULLSCREEN,
    Color,
    K_ESCAPE, K_b, K_c, K_g, K_l, K_o, K_r,
)

import paths
from gamelib import *


class Avatar(CameraTargetSprite):
    
    def __init__(self, map_pos, screen_pos):
        super(Avatar, self).__init__()
        self.image = pygame.surface.Surface((10,10))
        self.rect = self.image.get_rect()
        pygame.draw.circle(self.image, Color('yellow'), self.rect.center, 4)
        self.image.set_colorkey(Color('black'))
        self.position = map_pos
        self.screen_position = screen_pos


class App(Engine):
    
    def __init__(self, resolution=(640,640)):
        
        # Caption for window, and HUD in full-screen mode
        caption = (
            '16 Reduce Map Layers - G: grid | ' +
            'L: labels | R: reduced | C: collapsed | B: both | O: original'
        )
        
        resolution = Vec2d(resolution)
        
        super(App, self).__init__(
            caption=caption,
            camera_target=Avatar(resolution//2, resolution//2),
            resolution=resolution,
            frame_speed=0)
        
        # Load Tiled TMX map, then update the world and camera.
        self.original_map = toolkit.load_tiled_tmx_map('Gumm multi layer.tmx')
        State.map = self.original_map
        State.world.rect = State.map.rect.copy()
        # The map reduced.
        self.reduced_map = toolkit.reduce_map_layers(
            self.original_map, range(len(self.original_map.layers)))
        # The map collapsed.
        self.collapsed_map = toolkit.collapse_map(self.original_map, (8,8))
        # The map reduced and collapsed.
        self.collapsed_reduced_map = toolkit.collapse_map(self.reduced_map, (8,8))
        
        State.show_grid = True
        
        # I like huds. Add more stuff to the canned hud.
        toolkit.make_hud(caption)
        State.hud.add('Tile size', Statf(State.hud.next_pos(),
            'Tile size %s', callback=lambda:str(tuple(State.map.tile_size)),
            interval=2000))
        def screen_info():
            res = State.screen.size
            vis = State.camera.visible_tile_range[0]
            tiles = Vec2d(vis[2]-vis[0], vis[3]-vis[1])
            return 'Screen %dx%d / Visible tiles %dx%d' % (res.x,res.y,tiles.x,tiles.y,)
        State.hud.add('Screen', Stat(State.hud.next_pos(),
            '', callback=screen_info, interval=2000))
        def map_info():
            layern = len(State.map.layers)
            tilen = 0
            for layer in State.map.layers:
                tilen += len(layer)
            return '%d/%d' % (layern,tilen)
        State.hud.add('Layers/Tiles', Statf(State.hud.next_pos(),
            'Layers/Tiles: %s', callback=map_info, interval=2000))
        State.show_hud = True
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = State.camera.abs_screen_center
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        # Mouse and movement state. move_to is in world coordinates.
        self.move_to = None
        self.speed = None
        self.mouse_down = False
        
    def update(self):
        """overrides Engine.update"""
        # If mouse button is held down update for continuous walking.
        if self.mouse_down:
            self.update_mouse_movement(pygame.mouse.get_pos())
        self.update_camera_position()
        State.camera.update()
        State.hud.update()
        
    def update_mouse_movement(self, pos):
        # Angle of movement.
        angle = geometry.angle_of(self.speed_box.center, pos)
        # Final destination.
        self.move_to = None
        for edge in self.speed_box.edges:
            # line_intersects_line() returns False or (True,(x,y)).
            cross = geometry.line_intersects_line(edge, (self.speed_box.center, pos))
            if cross:
                x,y = cross[0]
                self.move_to = State.camera.screen_to_world(pos)
                self.speed = geometry.distance(
                    self.speed_box.center, (x,y)) / self.max_speed_box
                break
        
    def update_camera_position(self):
        """update the camera's position if any movement keys are held down
        """
        if self.move_to is not None:
            camera = State.camera
            wx,wy = camera.position
            # Speed formula.
            speed = self.speed * State.speed
            # If we're within spitting distance, then taking a full step would
            # overshoot the desired destination. Therefore, we'll jump there.
            if geometry.distance((wx,wy), self.move_to) < speed:
                wx,wy = self.move_to
                self.move_to = None
            else:
                # Otherwise, calculate the full step.
                angle = geometry.angle_of((wx,wy), self.move_to)
                wx,wy = geometry.point_on_circumference((wx,wy), speed, angle)
            # Keep avatar inside map bounds.
            rect = State.world.rect
            wx = max(min(wx,rect.right), rect.left)
            wy = max(min(wy,rect.bottom), rect.top)
            camera.position = wx,wy
        
    def draw(self):
        """overrides Engine.draw"""
        # Draw stuff.
        State.camera.interpolate()
        State.screen.clear()
        toolkit.draw_tiles()
        toolkit.draw_grid()
        toolkit.draw_labels()
        State.hud.draw()
        self.draw_avatar()
        State.screen.flip()
        
    def draw_avatar(self):
        camera = State.camera
        avatar = camera.target
        camera.surface.blit(avatar.image, camera.screen_center)
        
    def on_mouse_button_down(self, pos, button):
        self.mouse_down = True
        
    def on_mouse_button_up(self, pos, button):
        self.mouse_down = False
        
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        if key == K_g:
            State.show_grid = not State.show_grid
        elif key == K_l:
            State.show_labels = not State.show_labels
        elif key == K_r:
            State.map = self.reduced_map
        elif key == K_c:
            State.map = self.collapsed_map
        elif key == K_b:
            State.map = self.collapsed_reduced_map
        elif key == K_o:
            State.map = self.original_map
        elif key == K_ESCAPE:
            quit()
        
    def on_quit(self):
        quit()


if __name__ == '__main__':
    app = App()
    app.run()
