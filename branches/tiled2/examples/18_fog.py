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


__doc__ = """18_fog.py - A demo combining a Tiled Map Editor map, Gummworld2
Editor entities, and some fog images created with DR0ID's gradients module.

For the fog gradients: http://www.pygame.org/project-gradients-307-3051.html

# Here it is...
import math
import pygame
from pygame.locals import *
import gradients
pygame.init()
screen = pygame.display.set_mode((640,480))
screen_rect = screen.get_rect()
sp = list(screen_rect.center)
ep = [screen_rect.centerx,0]
cf = lambda x: math.cos(1.5*x)
af = lambda x: x**0.5
sizes = range(0, screen_rect.centery-100, (screen_rect.centery-100)/5)
for distance in sizes:
    ep[1] = distance
    screen.fill(Color('black'))
    gradients.draw_circle(screen, sp, ep, Color('black'), Color('white'),
        Rfunc=cf, Gfunc=cf, Bfunc=cf, Afunc=af,)
    radius = -screen_rect.centery + distance
    file = 'fog%d.png'%radius
    pygame.image.save(screen, file)
"""


import pygame
from pygame.sprite import Sprite
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import *
from gummworld2.geometry import RectGeometry, CircleGeometry, PolyGeometry


class Avatar(geometry.CircleGeometry):
    
    def __init__(self, map_pos, screen_pos):
        geometry.CircleGeometry.__init__(self, map_pos, 5)
        self.image = pygame.surface.Surface((10,10))
        pygame.draw.circle(self.image, Color('yellow'), (5,5), 4)
        self.image.set_colorkey(Color('black'))
        self.screen_position = screen_pos - 5


class App(Engine):
    
    def __init__(self, resolution=(640,480)):
        
        caption = '18 Fog - SPACE: Cycle fog radius'
        resolution = Vec2d(resolution)
        
        Engine.__init__(self,
            caption=caption,
            camera_target=Avatar((768,1065), resolution//2),
            resolution=resolution, ##display_flags=FULLSCREEN,
            frame_speed=0)
        
        self.map = TiledMap(data.filepath('map', 'mini2.tmx'))
        self.world = SpatialHash(self.map.rect, 32)
        self.set_state()
        
        entities,tilesheets = toolkit.load_entities(
            data.filepath('map', 'mini2.entities'))
        for e in entities:
            self.world.add(e)
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed. 800x600 has aspect ratio 8:6.
        self.speed_box = geometry.Diamond(0,0,8,6)
        self.speed_box.center = Vec2d(State.camera.rect.size) // 2
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        # Mouse and movement state. move_to is in world coordinates.
        self.move_to = None
        self.speed = None
#        self.target_moved = (0,0)
        self.mouse_down = False
        self.side_steps = []
        self.faux_avatar = Avatar(self.camera.target.position, 0)
        
        State.speed = 3
        
        self.fog = None
        self.fog_rect = None
        self.fogs = [
            pygame.image.load(data.filepath('image', name))
            for name in (
                'fog-128.png',
                'fog-156.png',
                'fog-184.png',
                'fog-212.png',
                'fog-240.png',
            )
        ]
        self.fogn = self.set_fog(0)
        
        # I like huds.
        toolkit.make_hud(caption)
        self.clock.schedule_interval(State.hud.update, 1.0)
    
    def update(self, dt):
        """overrides Engine.update"""
        # If mouse button is held down update for continuous walking.
        if self.mouse_down:
            self.update_mouse_movement(pygame.mouse.get_pos())
        self.update_camera_position()
        State.camera.update()
    
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
        """Step the camera's position if self.move_to contains a value.
        Handle collisions.
        """
        if self.move_to is not None:
            # Current position.
            camera = State.camera
            wx,wy = camera.position
            
            # Speed formula.
            speed = self.speed * State.speed
            
            # newx,newy is the new vector, which will be adjusted to avoid
            # collisions...
            
            if geometry.distance((wx,wy), self.move_to) < speed:
                # If within spitting distance, a full step would overshoot the
                # destination. Therefore, jump right to it.
                newx,newy = self.move_to
                self.move_to = None
            else:
                # Otherwise, calculate the full step.
                angle = geometry.angle_of((wx,wy), self.move_to)
                newx,newy = geometry.point_on_circumference((wx,wy), speed, angle)
            
            # Check world collisions.
            world = State.world
            camera_target = camera.target
            dummy = self.faux_avatar
            def can_step(step):
                dummy.position = step
                return not world.collideany(dummy)
            # Remove camera target so it's not a factor in collisions.
            move_ok = can_step((newx,newy))
            # We hit something. Try side-stepping.
            if not move_ok:
                newx = wx + pygame_utils.sign(newx-wx) * speed
                newy = wy + pygame_utils.sign(newy-wy) * speed
                for side_step in ((newx,wy),(wx,newy)):
                    move_ok = can_step(side_step)
                    if move_ok:
                        newx,newy = side_step
                        # End move_to if side-stepping backward from previous.
                        # This happens if we're trying to get through an
                        # obstacle with no valid path to take.
                        newstep = newx-wx,newy-wy
                        self.side_steps.append(newstep)
                        self.side_steps = self.side_steps[-2:]
                        for step in self.side_steps[:1]:
                            if step != newstep:
                                self.move_to = None
                                break
                        break
            else:
                del self.side_steps[:]
            
            # Either we can move, or not.
            if not move_ok:
                # Reset camera position.
                self.move_to = None
            else:
                # Keep avatar inside map bounds.
                rect = State.world.rect
                if newx < rect.left:
                    newx = rect.left
                elif newx > rect.right:
                    newx = rect.right
                if newy < rect.top:
                    newy = rect.top
                elif newy > rect.bottom:
                    newy = rect.bottom
                camera.position = newx,newy
    
    def draw(self, dt):
        """overrides Engine.draw"""
        # Draw stuff.
        State.screen.clear()
        toolkit.draw_tiles()
        self.draw_avatar()
        self.draw_fog()
        State.hud.draw()
        State.screen.flip()
    
    def draw_fog(self):
        State.screen.blit(self.fog, self.fog_rect,
            special_flags=BLEND_RGBA_MULT)
    
    def draw_avatar(self):
        camera = State.camera
        avatar = camera.target
        camera.surface.blit(avatar.image, avatar.screen_position)
    
    def set_fog(self, n):
        self.fog = self.fogs[n%len(self.fogs)]
        self.fog_rect = self.fog.get_rect(center=State.screen.center)
        return n
    
    def on_mouse_button_down(self, pos, button):
        self.mouse_down = True
    
    def on_mouse_button_up(self, pos, button):
        self.mouse_down = False
    
    def on_key_down(self, unicode, key, mod):
        # Turn on key-presses.
        if key == K_SPACE:
            self.fogn = self.set_fog(self.fogn+1)
        elif key == K_ESCAPE:
            context.pop()
    
    def on_quit(self):
        context.pop()
        
    # App.on_quit


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
