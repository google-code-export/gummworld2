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


"""17_load_and_use_world.py - A demo combining a Tiled Map Editor map and
Gummworld2 Editor entities.

NOTE: This is currently broken.
"""


import pygame
from pygame.sprite import Sprite
from pygame.locals import FULLSCREEN, Color, K_ESCAPE, K_TAB

import paths
import gummworld2
from gummworld2 import *
from gummworld2.geometry import RectGeometry, CircleGeometry, PolyGeometry


class Avatar(model.QuadTreeObject):
    
    def __init__(self, map_pos, screen_pos):
        self.image = pygame.surface.Surface((10,10))
        model.QuadTreeObject.__init__(self, self.image.get_rect(), map_pos)
        pygame.draw.circle(self.image, Color('yellow'), (5,5), 4)
        self.image.set_colorkey(Color('black'))
        self.screen_position = screen_pos - 5


class App(Engine):
    
    def __init__(self, resolution=(800,600)):
        
        resolution = Vec2d(resolution)
        
        Engine.__init__(self,
            caption='17 Load and Use World - TAB: Show World Geometry',
            camera_target=Avatar((450,770), resolution//2),
            resolution=resolution,
            frame_speed=0)
        
        self.map = toolkit.collapse_map(
            toolkit.load_tiled_tmx_map(data.filepath('map', 'mini2.tmx')),
            num_tiles=(9,8))
        self.world = model.WorldQuadTree(
            self.map.rect, worst_case=1000, collide_entities=True)
        self.set_state()
        
        entities,tilesheets = toolkit.load_entities(
            data.filepath('map', 'mini2.entities'))
        State.world.add(*entities)
        
        # I like huds.
        toolkit.make_hud()
        State.clock.schedule_update_priority(State.hud.update, 1.0)
        
        # Create a speed box for converting mouse position to destination
        # and scroll speed. 800x600 has aspect ratio 8:6.
        self.speed_box = geometry.Diamond(0,0,8,6)
        self.speed_box.center = Vec2d(State.camera.rect.size) // 2
        self.max_speed_box = float(self.speed_box.width) / 2.0
        
        # Mouse and movement state. move_to is in world coordinates.
        self.move_to = None
        self.speed = None
        self.target_moved = (0,0)
        self.mouse_down = False
        self.side_steps = []
        
        State.show_world = False
        State.speed = 3
        
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
        """Step the camera's position if self.move_to contains a value.
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
            dummy = model.QuadTreeObject(camera_target.rect.copy())
            def can_step(step):
                dummy.position = step
                world.add(dummy)
                collisions = [c[0] for c in world.collisions.keys()]
                world.remove(dummy)
                return dummy not in collisions
            # Remove camera target so it's not a factor in collisions.
            world.remove(camera_target)
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
                world.add(camera_target)
            else:
                # Keep avatar inside map bounds.
                rect = State.world.rect
                newx = max(min(newx,rect.right), rect.left)
                newy = max(min(newy,rect.bottom), rect.top)
                camera.position = newx,newy
                world.add(camera_target)
        
    def draw(self, dt):
        """overrides Engine.draw"""
        # Draw stuff.
        State.screen.clear()
        toolkit.draw_tiles()
        self.draw_world()
        State.hud.draw()
        self.draw_avatar()
        State.screen.flip()
        
    def draw_world(self):
        """Draw the on-screen shapes in the world.
        """
        if not State.show_world:
            return
        
        camera = State.camera
        camera_target = camera.target
        things = State.world.entities_in(camera.rect)
        display = camera.view.surface
        world_to_screen = camera.world_to_screen
        color = Color('white')
        
        draw_rect = pygame.draw.rect
        draw_circle = pygame.draw.circle
        draw_poly = pygame.draw.lines
        
        for thing in things:
            if thing is not camera_target:
                if isinstance(thing, RectGeometry):
                    r = thing.rect.copy()
                    r.center = world_to_screen(thing.position)
                    draw_rect(display, color, r, 1)
                elif isinstance(thing, CircleGeometry):
                    draw_circle(display, color,
                        world_to_screen(thing.position), thing.radius, 1)
                elif isinstance(thing, PolyGeometry):
                    points = [world_to_screen(p) for p in thing.points]
                    draw_poly(display, color, True, points)
    
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
        if key == K_TAB:
            State.show_world = not State.show_world
        elif key == K_ESCAPE:
            context.pop()
        
    def on_quit(self):
        context.pop()
        
    # App.on_quit


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
