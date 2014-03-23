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


__doc__ = """07_the_mana_world.py - An example of using a complex map from
The Mana World with the BasicMapRenderer in Gummworld2.

The demo includes collision detection and proper 2.5D placement of the avatar.

You need The Mana World maps from https://www.themanaworld.org/. Copy the TMX
map file and the data directory into the gummworld2/data directory.
   Gfx dir: graphics/ -> data/
   Maps:    *.tmx     -> data/map/
"""


import cProfile, pstats

import pygame
from pygame.sprite import Sprite
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import context, data, model, geometry, toolkit
from gummworld2 import Engine, State, TiledMap, BasicMapRenderer, Vec2d


class Avatar(model.Object):
    
    def __init__(self, map_pos):
        """Kind of a man-shaped guy."""
        model.Object.__init__(self)
        self.image = pygame.Surface((20,45))
        self.rect = self.image.get_rect()
        self.hitbox = Rect(0,0,20,5)
        pygame.draw.circle(self.image, Color('pink'), (10,10), 9)
        pygame.draw.circle(self.image, Color('darkblue'), (10,10), 10, 1)
        pygame.draw.rect(self.image, Color('lightblue'), (0,20,20,25))
        pygame.draw.rect(self.image, Color('darkblue'), (0,20,20,25), 1)
        self.image.set_colorkey(Color('black'))
        self.position = map_pos
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        # float pos
        self._position[:] = val
        x,y = val
        # my rect
        r = self.rect
        r.centerx = int(round(x))
        r.centery = int(round(y))
        # my hitbox
        r2 = self.hitbox
        r2.x = r.x
        r2.bottom = r.bottom


class App(Engine):
    
    def __init__(self, resolution=(640,480)):
        
        resolution = Vec2d(resolution)
        
        ## Load Tiled TMX map.
        """Looking at the map in Tiled, we see the following layers:
        tiled_map.layers[0] = Ground
        tiled_map.layers[1] = Fringe (where we'll put the avatar)
        tiled_map.layers[2] = Over
        tiled_map.layers[3] = Collision
        tiled_map.layers[4] = Object (which we won't do anything with)
        
        We need a strategy to draw the multi-layer architecture of this
        map design.
        
        1. Move the avatar, re-adding it to Fringe layer whenever it moves.
        2. We can test environment collisions versus the avatar's hitbox and
        the Collision layer.
        2. The BasicMapRenderer will draw the Ground layer.
        3. We will draw the layers that are above ground. Because the Fringe
        layer contains mobile objects we need to sort the tiles when drawing.
        """
        tiled_map = TiledMap(data.filepath('map', '001-1.tmx'))
        ## Save special layers.
        self.all_groups = tiled_map.layers[:]
        self.avatar_group = tiled_map.layers[1]
        self.collision_group = tiled_map.layers[3]
        self.overlays = tiled_map.layers[1:4]
        ## Hide the busy Collision layer. Player can show it by hitting K_3.
        self.collision_group.visible = False
        ## Remove above-ground layers so we can give map to the renderer.
        del tiled_map.layers[1:]
        
        ## The avatar is also the camera target.
        self.avatar = Avatar((650,690))
        
        Engine.__init__(self,
            caption='07 The Mana World Map -  0-9: layer',
            resolution=resolution,
            camera_target=self.avatar,
            map=tiled_map,
            frame_speed=0)
        
        ## Insert avatar into the Fringe layer.
        self.avatar_group.add(self.avatar)
        
        # I like huds.
        toolkit.make_hud()
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed.
        self.speed_box = geometry.Diamond(0,0,4,2)
        self.speed_box.center = Vec2d(State.camera.rect.size) // 2
        self.max_speed_box = float(self.speed_box.width) / 3.33
        
        # Mouse and movement state. move_to is in world coordinates.
        self.move_to = None
        self.speed = None
        self.target_moved = (0,0)
        self.mouse_down = False
        
        self.grid_cache = {}
        self.label_cache = {}
        
        State.speed = 3.33
        
        self.collision_dummy = Avatar((0,0))
        
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
            dist = geometry.distance((wx,wy), self.move_to)
            if dist < speed:
                wx,wy = self.move_to
                self.move_to = None
            else:
                # Otherwise, calculate the full step.
                angle = geometry.angle_of((wx,wy), self.move_to)
                wx,wy = geometry.point_on_circumference((wx,wy), speed, angle)
            # Check collision with environment.
            avatar = self.avatar
            dummy = self.collision_dummy
            dummy.position = wx,wy
            get_objects = self.collision_group.objects.intersect_objects
            ## Collision handling.
            hits = get_objects(dummy.hitbox)
            if not hits:
                pass
            else:
                # Try move x
                dummy.position = wx,avatar.position.y
                hits = get_objects(dummy.hitbox)
                if not hits:
                    wy = avatar.position.y
                else:
                    # Try move y
                    dummy.position = avatar.position.x,wy
                    hits = get_objects(dummy.hitbox)
                    if not hits:
                        wx = avatar.position.x
                    else:
                        # Can't move
                        self.move_to = None
                        return
            # Keep avatar inside map bounds.
            rect = State.world.rect
            wx = max(min(wx,rect.right), rect.left)
            wy = max(min(wy,rect.bottom), rect.top)
            camera.position = wx,wy
            self.avatar_group.add(avatar)
    
    def toggle_layer(self, i):
        """toggle visibility of layer i"""
        try:
            layer = self.all_groups[i]
            layer.visible = not layer.visible
            self.renderer.clear()
        except:
            pass
    
    def draw(self, interp):
        """overrides Engine.draw"""
        # Draw stuff.
        State.screen.clear()
        ## Renderer draws ground tiles.
        self.renderer.draw_tiles()
        ## Overlay ground with detail tiles.
        self.draw_detail()
        if False: self.draw_debug()
        State.hud.draw()
        State.screen.flip()
    
    def draw_detail(self):
        camera = State.camera
        camera_rect = camera.rect
        cx,cy = camera_rect.topleft
        blit = camera.surface.blit
        avatar = self.avatar
        # Draw static overlay tiles.
        for layer in self.overlays:
            sprites = layer.objects.intersect_objects(camera_rect)
            if layer.visible:
                if layer is self.avatar_group:
                    sprites.sort(key=lambda o:o.rect.bottom)
                for s in sprites:
                    if s is avatar:
                        blit(s.image, s.rect.move(camera.anti_interp(s)))
                    else:
#                        sx,sy = s.rect.topleft
                        blit(s.image, s.rect.move(-cx,-cy))
    
    def draw_debug(self):
        # draw the hitbox and speed box
        camera = State.camera
        cx,cy = camera.rect.topleft
        rect = self.avatar.hitbox
        pygame.draw.rect(camera.surface, Color('red'), rect.move(-cx,-cy))
        pygame.draw.polygon(camera.surface, Color('white'), self.speed_box.corners, 1)
    
    def on_mouse_button_down(self, pos, button):
        self.mouse_down = True
    
    def on_mouse_button_up(self, pos, button):
        self.mouse_down = False
    
    def on_key_down(self, unicode, key, mod):
        if key == K_ESCAPE:
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
