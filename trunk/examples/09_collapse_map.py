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
from pygame.locals import (
    FULLSCREEN,
    Color,
    K_TAB, K_ESCAPE, K_g, K_l, K_0, K_1, K_2, K_9,
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
    
    def __init__(self, resolution=(800,600)):
        
        # Caption for window, and HUD in full-screen mode
        caption = (
            '09 pymunk Bounding Box - TAB: view | G: grid | ' +
            'L: labels | Collapse: 1-10 (0 is 10)'
        )
        
        resolution = Vec2d(resolution)
        
        super(App, self).__init__(
            caption=caption,
            camera_target=Avatar((325,420), resolution//2),
            resolution=resolution,
            display_flags=FULLSCREEN,
            frame_speed=0)
        
        # Load Tiled TMX map, then update the world and camera.
        self.map = toolkit.load_tiled_tmx_map('Gumm no swamps.tmx')
        State.map = self.map
        State.world.rect = State.map.rect.copy()
        # The collapse stat for the hud.
        self.collapse = 1
        
        # Save the main state.
        State.save('main', ['camera'])
        
        # The rect that defines the screen subsurface. It will also be used to
        # draw a border around the subsurface.
        self.view_rect = pygame.Rect(30,20,*State.screen.size*2//3)
        
        # Set up the subsurface as the camera's drawing surface.
        subsurface = State.screen.surface.subsurface(self.view_rect)
        State.camera = Camera(State.camera.target, subsurface)
        State.name = 'small'
        State.save(State.name, ['camera'])
        State.restore('main', ['camera'])
        
        # Easy way to select the "next" state name.
        self.next_state = {
            'main' : 'small',
            'small' : 'main',
        }
        
        # I like huds.
        toolkit.make_hud(caption)
        State.hud.add('Collapse', Statf(State.hud.next_pos(),
            'Collapse %d', callback=lambda:self.collapse,
            interval=2000))
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
        State.show_hud = True
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = self.view_rect.center
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
        if State.name == 'small':
            pygame.draw.rect(State.screen.surface, (99,99,99), self.view_rect, 1)
        State.screen.flip()
        
    def draw_avatar(self):
        camera = State.camera
        avatar = camera.target
        camera.surface.blit(avatar.image, avatar.screen_position)
        
    def update_mouse_movement(self, pos):
        # Angle of movement.
        angle = geometry.angle_of(self.speed_box.center, pos)
        # Final destination.
        self.move_to = None
        for edge in self.speed_box.edges:
            # line_intersects_line() returns False or (True,(x,y)).
            cross = geometry.line_intersects_line(edge, (self.speed_box.center, pos))
            if cross:
                x,y = cross[1]
                self.move_to = State.camera.screen_to_world(pos)
                ## BUG IN SPEED
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
        
    def on_mouse_button_down(self, pos, button):
        self.mouse_down = True
        
    def on_mouse_button_up(self, pos, button):
        self.mouse_down = False
        
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        if key == K_TAB:
            # Select the next state name and and restore it.
            State.restore(self.next_state[State.name], ['camera'])
            if State.name == 'small':
                self.speed_box.center = self.view_rect.center
            else:
                self.speed_box.center = State.screen.rect.center
        elif key == K_g:
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
            quit()
        
    def on_quit(self):
        quit()


if __name__ == '__main__':
    app = App()
    app.run()
