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


"""09_collapse_map.py - An example of using toolkit.collapse_map in Gummworld2.

This demo does not use pymunk.

The results of this demo can be impressive on computers with fast CPUs.

Maps with many small tiles are great for designing maps with interesting detail.
But they take a lot longer for Python to process than larger tiles because there
are more objects in the working lists. toolkit.collapse_map() can help with
this.

The function takes a map with many small tiles and converts it to a map with
fewer, larger tiles for more efficient processing.

While running this demo use keys 0-9 to set the collapse level. 1 presents the
original map of 32x32 size tiles, 2 is double the tile size, and so on. 0
presents a map collapsed 10 times, or 320x320 pixel per tile.

Watch what happens to the frame rate as tile size increases.
"""


import pygame
from pygame.sprite import Sprite
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import context, data, model, geometry, toolkit
from gummworld2 import Engine, State, CameraTargetSprite, Vec2d, Stat, Statf


class Avatar(CameraTargetSprite):
    
    def __init__(self, map_pos, screen_pos):
        CameraTargetSprite.__init__(self)
        self.image = pygame.Surface((10,10))
        self.rect = self.image.get_rect()
        pygame.draw.circle(self.image, Color('yellow'), self.rect.center, 4)
        self.image.set_colorkey(Color('black'))
        self.position = map_pos
        self.screen_position = screen_pos


class App(Engine):
    
    def __init__(self, resolution=(800,600)):
        
        # Caption for window, and HUD in full-screen mode
        caption = (
            '09 Collapse Map - TAB: view | G: grid | ' +
            'L: labels | Collapse: 1-10 (0 is 10)'
        )
        
        resolution = Vec2d(resolution)
        
        Engine.__init__(self,
            caption=caption,
            camera_target=Avatar((325,420), resolution//2),
            resolution=resolution,
            display_flags=FULLSCREEN,
            frame_speed=0, default_schedules=False)
        
        # Load Tiled TMX map, then update the world and camera.
        self.map = toolkit.load_tiled_tmx_map(
            data.filepath('map', 'Gumm no swamps.tmx'))
        self.world = model.NoWorld(self.map.rect)
        self.set_state()
        self.schedule_default()
        # The collapse stat for the hud.
        self.collapse = 1
        
        # I like huds. Add more stuff to the canned hud.
        toolkit.make_hud(caption)
        State.hud.add('Collapse', Statf(State.hud.next_pos(),
            'Collapse %d', callback=lambda:self.collapse,
            interval=2.))
        State.hud.add('Tile size', Statf(State.hud.next_pos(),
            'Tile size %s', callback=lambda:str(tuple(State.map.tile_size)),
            interval=2.))
        def screen_info():
            visible_tiles = State.camera.visible_tile_range
            res = State.screen.size
            if len(visible_tiles):
                vis = visible_tiles[0]
                tiles = Vec2d(vis[2]-vis[0], vis[3]-vis[1])
            else:
                tiles = Vec2d(0,0)
            return 'Screen %dx%d / Visible tiles %dx%d' % (res.x,res.y,tiles.x,tiles.y,)
        State.hud.add('Screen', Stat(State.hud.next_pos(),
            '', callback=screen_info, interval=2.))
        State.clock.schedule_update_priority(State.hud.update, 1.0)
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = State.camera.abs_screen_center
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        # Mouse and movement state. move_to is in world coordinates.
        self.move_to = None
        self.speed = None
        self.mouse_down = False
        
    def update(self, dt):
        """overrides Engine.update"""
        # If mouse button is held down update for continuous walking.
        if self.mouse_down:
            self.update_mouse_movement(pygame.mouse.get_pos())
        self.update_camera_position()
        
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
        
    def draw(self, dt):
        """overrides Engine.draw"""
        # Draw stuff.
        State.screen.clear()
        toolkit.draw_tiles()
        toolkit.draw_grid()
        toolkit.draw_labels()
        State.hud.draw()
        self.draw_avatar()
        if State.name == 'small':
            pygame.draw.rect(State.screen.surface, (99,99,99),
            State.camera.view.parent_rect, 1)
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
        elif key == K_1:
            State.map = self.map
        elif key in [K_0]+range(K_2,K_9+1):
            if key == K_0:
                n = 10
            else:
                n = key - K_0
            State.map = toolkit.collapse_map(self.map, (n,n))
            State.world.rect = State.map.rect.copy()
            self.collapse = n
        elif key == K_ESCAPE:
            context.pop()
        
    def on_quit(self):
        context.pop()


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
