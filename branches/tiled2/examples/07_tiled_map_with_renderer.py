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
__author__ = 'Gummbum, (c) 2011-2013'


__doc__ = """07_tiled_map_with_renderer.py - An example of using Tiled maps with
the BasicMapRenderer in Gummworld2.

This demo uses small tiles from a tileset distributed with Tiled 0.7.2,
the Java version. It gets around the lower performance of small tiles by
blitting them to an intermediate set of larger tiles.

Only three changes are required to use the renderer:
    
    1. Create the renderer, passing it the map and scroll speed.
    2. Call renderer.set_rect() once per tick to update its view rect.
    3. Call renderer.draw_tiles() once per frame.

Thanks to the creators of Tiled Map Editor:
    http://www.mapeditor.org/

Thanks to dr0id for his nice tiledtmxloader module:
    http://www.pygame.org/project-map+loader+for+%27tiled%27-1158-2951.html
"""


import sys
import cProfile, pstats

import pygame
from pygame.sprite import Sprite
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import context, data, model, geometry, toolkit
from gummworld2 import Engine, State, TiledMap, BasicMapRenderer, Vec2d


class Avatar(model.Object):
    
    def __init__(self, map_pos, screen_pos):
        model.Object.__init__(self)
        self.image = pygame.Surface((10,10))
        self.rect = self.image.get_rect()
        pygame.draw.circle(self.image, Color('yellow'), self.rect.center, 4)
        self.image.set_colorkey(Color('black'))
        self.position = map_pos
        self.screen_position = screen_pos


class App(Engine):
    
    def __init__(self, resolution=(640,480)):
        
        resolution = Vec2d(resolution)
        
        ## Load Tiled TMX map, then update the world's dimensions.
        try:
            tiled_map = TiledMap(data.filepath('map', 'Gumm no swamps.tmx'))
        except pygame.error:
            print 'Sorry! Gummworld2 cannot include The Mana World assets due to licensing.'
            print 'To use this demo please download gummworld2_tmw.zip and follow its instructions.'
            sys.exit()
        
        Engine.__init__(self,
            caption='07 Tiled Map with Renderer -  G: grid | L: labels | 0-9: layer',
            resolution=resolution,
            camera_target=Avatar((325,420), resolution//2),
            map=tiled_map,
            frame_speed=0)
        
        # I like huds.
        toolkit.make_hud()
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = Vec2d(State.camera.rect.size) // 2
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        # Mouse and movement state. move_to is in world coordinates.
        self.move_to = None
        self.speed = None
        self.target_moved = (0,0)
        self.mouse_down = False
        
        self.grid_cache = {}
        self.label_cache = {}
        
        State.speed = 3.33
        
        ## Create the renderer.
        self.renderer = BasicMapRenderer(
            tiled_map, max_scroll_speed=State.speed)
    
    def update(self, dt):
        """overrides Engine.update"""
        # If mouse button is held down update for continuous walking.
        if self.mouse_down:
            self.update_mouse_movement(pygame.mouse.get_pos())
        self.update_camera_position()
        State.camera.update()
        ## Set render's rect.
        self.renderer.set_rect(center=State.camera.rect.center)
        State.hud.update(dt)
    
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
    
    def toggle_layer(self, i):
        """toggle visibility of layer i"""
        try:
            layer = State.map.layers[i]
            layer.visible = not layer.visible
            self.renderer.clear()
        except:
            pass
    
    def draw(self, interp):
        """overrides Engine.draw"""
        # Draw stuff.
        State.screen.clear()
        ## Renderer draws tiles.
        self.renderer.draw_tiles()
        if State.show_grid:
            toolkit.draw_grid(self.grid_cache)
        if State.show_labels:
            toolkit.draw_labels(self.label_cache)
        State.hud.draw()
        self.draw_avatar()
        State.screen.flip()
    
    def draw_avatar(self):
        camera = State.camera
        avatar = camera.target
        camera.surface.blit(avatar.image, avatar.screen_position)
    
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
        elif key == K_ESCAPE:
            context.pop()
        elif key >= K_0 and key <= K_9:
            self.toggle_layer(key - K_0)
    
    def on_quit(self):
        context.pop()


def main():
    app = App()
    gummworld2.run(app)


if __name__ == '__main__':
    if False:
        cProfile.run('main()', 'prof.dat')
        p = pstats.Stats('prof.dat')
        p.sort_stats('time').print_stats()
    else:
        main()
