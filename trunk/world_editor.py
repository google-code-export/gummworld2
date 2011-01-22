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


"""world_editor.py - A world editor for Gummworld2.
"""


import cProfile
import pstats
import os
from os.path import join as joinpath, normpath
import sys
import time

import pygame
from pygame.locals import *
try:
    import pymunk
except:
    pymunk = None

import paths
from gamelib import *
import gui


#os.environ['SDL_VIDEO_CENTERED'] = '1'


menu_data = (
    'Main',
    'Grid',
    'Labels',
    'HUD',
    (
        'Geometry',
        'Line',
        'Triangle',
        'Quad',
        'Poly',
        'Select Region',
        'Resize',
        'Delete',
    ),
    (
        'Tiling',
        'Load Tileset',
        'Pick from Palette',
        'Pick from Screen',
        'Paint',
        'Erase',
        'Select Region',
        'Fill',
    ),
    (
        'Map',
        'New',
        'Load',
        'Save',
    ),
    'Quit',
)


class ControlPoint(Rect):
    """Control point that can be used to manipulate a geometric object.
    """
    
    image = None
    
    def __init__(self, parent, attr):
        super(ControlPoint, self).__init__(0,0,7,7)
        if self.image is None:
            self.image = pygame.surface.Surface((7,7))
            self.image.fill(Color('yellow'))
        self.parent = parent
        self.attr = attr
        
    # ControlPoint.__init__
    
    @property
    def position(self):
        return self.center
    @position.setter
    def position(self, val):
        x,y = val
        self.center = round(x),round(y)
        self.parent.adjust(self, self.attr)
        
    # ControlPoint.position

class RectGeom(geometry.RectGeometry):
    
    draw_rect = pygame.draw.rect
    
    def __init__(self, *args, **kw):
        super(RectGeom, self).__init__(*args, **kw)
        self._attrs = 'topleft','topright','bottomright','bottomleft','center'
        self._cp = [ControlPoint(self, self._attrs[i]) for i in range(5)]
        self.grabbed = None
        
    # RectGeom.__init__
    
    @property
    def control_points(self):
        controls = self._cp
        r = self.rect
        attrs = self._attrs
        for i,cp in enumerate(controls):
            cp.center = getattr(r, attrs[i])
        return controls
        
    # RectGeom.control_points
    
    def grab(self, mouse_rect):
        for cp in self.control_points:
            if cp.colliderect(mouse_rect):
                self.grabbed = cp
                return True
        self.grabbed = None
        return False
        
    # RectGeom.grab
    
    def release(self):
        self.grabbed = None
        
    # RectGeom.release
    
    def adjust(self, cp, attr):
        if attr != 'center':
            val = Vec2d(getattr(self.rect, attr))
            diff = cp.center - val
            if attr in ('topleft','bottomleft'):
                diff.x = -diff.x
            if attr in ('topleft','topright'):
                diff.y = -diff.y
            self.rect.inflate_ip(diff)
        setattr(self.rect, attr, cp.center)
        
    # RectGeom.adjust
    
    def draw(self):
        app = State.app
        camera = State.camera
        surface = camera.surface
        world_to_screen = camera.world_to_screen
        if self in app.mouseover_shapes:
            color = Color('white')
        else:
            color = Color('grey')
        r = self.rect.copy()
        r.center = world_to_screen(self.rect.center)
        self.draw_rect(surface, color, r, 1)
        if self is app.selected:
            for cp in self.control_points:
                surface.blit(cp.image, world_to_screen(cp.topleft))
        
    # RectGeom.draw


class PolyGeom(geometry.PolyGeometry):
    
    draw_poly = pygame.draw.polygon
    draw_rect = pygame.draw.rect
    
    def __init__(self, *args, **kw):
        super(PolyGeom, self).__init__(*args, **kw)
        
        self._points = [Vec2d(p) for p in self._points]
        
        self.tmp_rect = self.rect.copy()
        self._cp = [ControlPoint(self, i) for i in range(len(self._points)+1)]
        self._cp = self.control_points
        self.grabbed = None
        
    # PolyGeom.__init__
    
    @property
    def control_points(self):
        controls = self._cp
        points = self.points
        for i,p in enumerate(points):
            controls[i].center = p
        i += 1
        controls[i].center = self.rect.center
        return controls
        
    # PolyGeom.control_points
    
    def grab(self, mouse_rect):
        for cp in self.control_points:
            if cp.colliderect(mouse_rect):
                self.grabbed = cp
                return True
        self.grabbed = None
        return False
        
    # PolyGeom.grab
    
    def release(self):
        self.grabbed = None
        
    # PolyGeom.release
    
    def adjust(self, cp, i):
        controls = self._cp
        
        if cp is controls[-1]:
            # Center control grabbed. Just move rect.
            self.position = cp.center
        else:
            # Poly point grabbed. Recalculate rect.
            controls = controls[:-1]
            xvals = [c.centerx for c in controls]
            yvals = [c.centery for c in controls]
            xmin = reduce(min, xvals)
            width = reduce(max, xvals) - xmin + 1
            ymin = reduce(min, yvals)
            height = reduce(max, yvals) - ymin + 1
            self.rect.topleft = xmin,ymin
            self.rect.size = width,height
            
            # Recalculate local points relative to rect.
            topleft = Vec2d(xmin,ymin)
            points = self._points
            for i,c in enumerate(controls):
                points[i] = c.center - topleft
        
    # PolyGeom.adjust
    
    def draw(self):
        app = State.app
        camera = State.camera
        surface = camera.surface
        world_to_screen = camera.world_to_screen
        if self in app.mouseover_shapes:
            color = Color('white')
        else:
            color = Color('grey')
        self.draw_rect(surface, Color('grey'), self.rect, 1)
        pos = world_to_screen(self.rect.topleft)
        points = [p+pos for p in self._points]
        self.draw_poly(surface, color, points, 1)
        if self is app.selected:
            for cp in self.control_points:
                surface.blit(cp.image, world_to_screen(cp.topleft))
        
    # PolyGeom.draw

class CircleGeom(geometry.CircleGeometry):
    
    draw_circle = pygame.draw.circle
    draw_rect = pygame.draw.rect
    
    def __init__(self, *args, **kw):
        super(CircleGeom, self).__init__(*args, **kw)
        self._attrs = 'origin','radius'
        self._cp = [ControlPoint(self, self._attrs[i]) for i in range(2)]
        self.grabbed = None
        
    # CircleGeom.__init__
    
    @property
    def control_points(self):
        controls = self._cp
        r = self.rect
        controls[0].center = self.rect.center
        controls[1].center = geometry.point_on_circumference(
            self.origin, self.radius, 180.0)
        return controls
        
    # CircleGeom.control_points
    
    def grab(self, mouse_rect):
        for cp in self.control_points:
            if cp.colliderect(mouse_rect):
                self.grabbed = cp
                return True
        self.grabbed = None
        return False
        
    # CircleGeom.grab
    
    def release(self):
        self.grabbed = None
        
    # CircleGeom.release
    
    def adjust(self, cp, attr):
        if attr == 'origin':
            self.position = cp.center
        elif attr == 'radius':
            self.radius = geometry.distance(self.origin, cp.center)
        
    # CircleGeom.adjust
    
    def draw(self):
        app = State.app
        camera = State.camera
        surface = camera.surface
        world_to_screen = camera.world_to_screen
        if self in app.mouseover_shapes:
            color = Color('white')
        else:
            color = Color('grey')
        self.draw_rect(surface, Color('grey'), self.rect, 1)
        self.draw_circle(surface, color, self.origin, self.radius, 1)
        if self is app.selected:
            for cp in self.control_points:
                surface.blit(cp.image, world_to_screen(cp.topleft))
        
    # CircleGeom.draw


class MapEditor(object):
    """The Beast.
    """
    
    def __init__(self):
        
        State.app = self
        
        tile_size = 128,128
        map_size = 10,10
        
        ## I hate this kludge...
#        screen_size = Vec2d(pygame.display.list_modes()[0]) - (20,70)
        screen_size = Vec2d(1024,768)
        os.environ['SDL_VIDEO_WINDOW_POS'] = '7,30'
        
        # Set up the Gummworld2 state.
        State.screen = Screen(screen_size, RESIZABLE)
        State.map = Map(tile_size, map_size)
        State.camera = Camera(
            model.QuadTreeObject(Rect(0,0,5,5), ),
            View(State.screen.surface, Rect(0,0,screen_size.x*2/3,screen_size.y))
        )
        State.world = model.WorldQuadTree(
            State.map.rect, worst_case=99, collide_entities=True)
        State.clock = GameClock(30, 0)
        State.camera.position = State.camera.view.center
        
        # Mouse details.
        self.mouse_shape = RectGeom(0,0,5,5)
        self.mouse_down = 0
        self.selected = None
        self.mouseover_shapes = []
        
        # Make a gooey.
        self.make_gui()
        
        # Make some default content and HUD.
        toolkit.make_tiles2()
        make_hud()
        State.show_hud = True
        State.show_grid = True
        State.show_labels = True
        
    # MapEditor.__init__
    
    def gui_hover(self):
        self = State.app
        if self.menus.is_hovering():          return self.menus
        elif self.tool_table.is_hovering():   return self.toolbar
        elif self.h_map_slider.is_hovering(): return self.h_map_slider
        elif self.v_map_slider.is_hovering(): return self.v_map_slider
        else:
            for m in self.menus.widgets:
                if m.options.is_open():
                    return m.options
                    break
        return None
        
    # MapEditor.gui_hover
    
    def make_gui(self):
        # Make the GUI.
        self.gui = gui.App(theme=gui.Theme(dirs=['data/themes/default']))
        width,height = State.screen.size
        c = gui.Container(width=width,height=height)
        
        # Menus.
        self.menus = make_menus(self)
        c.add(self.menus, 1, 1)
        self.menus.rect.w,self.menus.rect.h = self.menus.resize()
        
        # Toolbar.
        self.toolbar,self.tool_table = make_toolbar(self)
        x = self.menus.rect.right + 2
        c.add(self.tool_table, x, 0)
        
        # Scrollbars for scrolling map.
        self.make_scrollbars(c)
        
        # Gogogo GUI.
        self.gui.init(widget=c, screen=State.screen.surface)
        
    # MapEditor.make_gui
    
    def make_scrollbars(self, c):
        """Make (or remake after resize event) map scrollbars to fit the window.
        """
        view_rect = State.camera.view.parent_rect
        w,h = view_rect.size
        thick = 15
        
        #   H-slider.
        minv = view_rect.centerx - thick
        maxv = State.map.tile_size.x * State.map.map_size.x - minv + thick
        size = max(round(float(w) / State.map.rect.w * w), 25)
        if hasattr(self, 'h_map_slider'):
            val = self.h_map_slider.value
        else:
            val = view_rect.centerx
        #   val, min, max, len-px, step
        self.h_map_slider = gui.HSlider(val,minv,maxv,size,
            name='h_map_slider', width=w-thick, height=thick)
        self.h_map_slider.rect.bottomleft = view_rect.bottomleft
        c.add(self.h_map_slider, *self.h_map_slider.rect.topleft)
        
        #   V-slider.
        minv = view_rect.centery - self.menus.rect.bottom - 3
        maxv = State.map.tile_size.y * State.map.map_size.y - minv + thick
        size = max(round(float(h) / State.map.rect.h * h), 25)
        if hasattr(self, 'v_map_slider'):
            val = self.v_map_slider.value
        else:
            val = view_rect.centery
        #   val, min, max, len-px, step
        self.v_map_slider = gui.VSlider(val,minv,maxv,size,
            name='v_map_slider', height=h-thick, width=thick)
        self.v_map_slider.rect.topright = view_rect.topright
        c.add(self.v_map_slider, *self.v_map_slider.rect.topleft)
        
    # MapEditor.make_sliders
    
    def run(self):
        State.running = True
        while State.running:
            pygame.time.wait(5)
            State.clock.tick()
            self.get_events()
            self.update()
            State.world.step()
            self.draw()
        
    # MapEditor.run
    
    def update(self):
        """Overrides Engine.update."""
        State.camera.update()
        self.update_gui()
        self.update_shapes()
        if State.show_hud:
            State.hud.update()
        
    # MapEditor.update
    
    def update_gui(self):
        # Plucked from gui.App.loop().
        gui = self.gui
        gui.set_global_app()
        gui.update()
        State.camera.position = self.h_map_slider.value,self.v_map_slider.value
        
    # MapEditor.update_gui
    
    def update_shapes(self):
        ## Failing when shape is centered at 265,362@2
        mouse_shape = self.mouse_shape
        self.mouseover_shapes = [shape for ent,shape in State.world.collisions
            if ent is mouse_shape
        ]
        
    # MapEditor.update_gui
    
    def draw(self):
        """Overrides Engine.draw."""
        # Draw stuff.
        State.camera.interpolate()
        State.camera.view.clear()
        toolkit.draw_tiles()
        toolkit.draw_labels()
        toolkit.draw_grid()
        self.draw_world()
        if State.show_hud:
            State.hud.draw()
        self.gui.paint()
        State.screen.flip()
        
    # MapEditor.draw
    
    def draw_world(self):
        mouse_shape = self.mouse_shape
        things = State.world.entities_in(State.camera.rect)
        for thing in things:
            if thing is not mouse_shape:
                thing.draw()
        
    # MapEditor.draw_world
    
    ## Mouse Actions ##
    
    def deselect(self):
        if self.selected:
            self.selected.release()
            self.selected = None
        
    # MapEditor.deselect
    
    def action_mouse_click(self, e):
        if self.mouse_down == 3:
            # Put a shape.
            pos = State.camera.screen_to_world(e.pos)
            shape = self.toolbar.value
            if shape == 'rect_tool':
                geom = RectGeom(0,0,30,30, pos)
            elif shape == 'triangle_tool':
                geom = PolyGeom([(14,0),(29,29),(0,29)], pos)
            elif shape == 'quad_tool':
                geom = PolyGeom([(0,0),(25,0),(29,29),(0,29)], pos)
            elif shape == 'poly_tool':
                geom = PolyGeom([(14,0),(29,12),(23,29),(7,29),(0,12)], pos)
            elif shape == 'circle_tool':
                geom = CircleGeom(pos, 20)
            self.selected = geom
            State.world.add(geom)
        elif self.mouse_down == 1:
            mouseover_shapes = self.mouseover_shapes
            if self.selected not in mouseover_shapes:
                self.deselect()
                if len(mouseover_shapes):
                    self.selected = mouseover_shapes[0]
            elif self.selected is not None:
                if self.selected.grab(self.mouse_shape):
                    # Grabbed control point.
                    pass
                elif len(mouseover_shapes):
                    # Select next shape under cursor.
                    i = mouseover_shapes.index(self.selected)
                    i += 1
                    if i >= len(mouseover_shapes):
                        i = 0
                    self.selected = mouseover_shapes[i]
        
    # MapEditor.action_mouse_click

    def action_mouse_drag(self, e):
        if self.selected:
            if self.mouse_down == 3:
                # Move the selected shape.
                self.selected.position = State.camera.screen_to_world(e.pos)
                State.world.add(self.selected)
            elif self.mouse_down == 1:
                # Resize the selected shape.
                grabbed = self.selected.grabbed
                if grabbed is not None:
                    grabbed.position = State.camera.screen_to_world(e.pos)
                    State.world.add(grabbed.parent)
        
    # MapEditor.action_mouse_drag

    def action_mouse_release(self, e):
        # To be determined.
        if self.selected:
            self.selected.release()
        
    # MapEditor.action_mouse_release
    
    ## Menu Actions ##
    
    def new_map(self, *args):
        print 'new_map'
    def open_map(self, *args):
        print 'open_map'
    def save_map(self, *args):
        print 'save_map'
    def save_as_map(self, *args):
        print 'save_as_map'
    def quit_app(self, *args):
        quit()
    def toggle_grid(self, *args):
        State.show_grid = not State.show_grid
    def toggle_labels(self, *args):
        State.show_labels = not State.show_labels
    def toggle_hud(self, *args):
        State.show_hud = not State.show_hud
    
    def get_events(self):
        mm = None
        for e in pygame.event.get():
            typ = e.type
            if typ == KEYDOWN:
                self.on_key_down(e, e.unicode, e.key, e.mod)
            elif typ == KEYUP:
                self.on_key_up(e, e.key, e.mod)
            elif typ == MOUSEMOTION:
                mm = e
            elif typ == MOUSEBUTTONUP:
                self.on_mouse_button_up(e, e.pos, e.button)
            elif typ == MOUSEBUTTONDOWN:
                self.on_mouse_button_down(e, e.pos, e.button)
            elif typ == VIDEORESIZE:
                self.on_resize(e, e.size, e.w, e.h)
            elif typ == QUIT:
                    self.on_quit()
        if mm is not None:
            self.on_mouse_motion(mm, mm.pos, mm.rel, mm.buttons)
        
    # MapEditor.get_events
    
    def on_key_down(self, e, unicode, key, mod):
        # Maybe some accelerator keys or something.
        self.gui.event(e)
        
    # MapEditor.on_key_down
    
    def on_key_up(self, e, key, mod):
        # Maybe some accelerator keys or something.
        self.gui.event(e)
        
    # MapEditor.on_key_up
    
    def on_mouse_button_down(self, e, pos, button):
        if self.mouse_down:
            # Multi-button does nothing.
            return
        self.gui.event(e)
        if self.gui_hover():
            # GUI connection would have dispatched it.
            return
        else:
            self.mouse_down = button
            self.action_mouse_click(e)
        
    # MapEditor.on_mouse_button_down
    
    def on_mouse_motion(self, e, pos, rel, buttons):
        self.gui.event(e)
        self.mouse_shape.position = State.camera.screen_to_world(pos)
        State.world.add(self.mouse_shape)
        if self.mouse_down:
            # Crossing GUI widgets does not interfere with dragging.
            self.action_mouse_drag(e)
        
    # MapEditor.on_mouse_motion
    
    def on_mouse_button_up(self, e, pos, button):
        self.gui.event(e)
        if self.mouse_down:
            # Crossing GUI widgets does not interfere with drag-and-release.
            if self.mouse_down == button:
                self.action_mouse_release(e)
                self.mouse_down = 0
        
    # MapEditor.on_mouse_button_up
    
    def on_resize(self, e, screen_size, w, h):
        # Update the pygame display mode and Gummworld2 camera view.
        width,height = w,h
        State.screen = Screen(screen_size, RESIZABLE)
        State.camera.view = View(State.screen.surface, Rect(0,0,w*2/3,h))
        
        # Resize the widgets.
        self.gui.widget.resize(width=w, height=h)
        c = self.gui.widget
        c.remove(self.h_map_slider)
        c.remove(self.v_map_slider)
        self.make_scrollbars(c)
        
    # MapEditor.init_size
    
    def on_quit(self):
        quit()
        
    # MapEditor.on_quit


def make_hud(caption=None):
    """Create a HUD with dynamic items.
    """
    State.hud = HUD()
    State.hud.x += 20
    State.hud.i += 3
    next_pos = State.hud.next_pos
    
    if caption:
        State.hud.add('Caption', Stat(next_pos(), caption))
    
    State.hud.add('FPS',
        Statf(next_pos(), 'FPS %d', callback=State.clock.get_fps))
    
    rect = State.world.rect
    l,t,r,b = rect.left,rect.top,rect.right,rect.bottom
    State.hud.add('Bounds',
        Stat(next_pos(), 'Bounds %s'%((int(l),int(t),int(r),int(b)),)) )
    
    def get_mouse():
        s = pygame.mouse.get_pos()
        w = State.camera.screen_to_world(s)
        return 'S'+str(s) + ' W'+str((int(w.x),int(w.y),))
    State.hud.add('Mouse',
        Statf(next_pos(), 'Mouse %s', callback=get_mouse, interval=100))
    
    def get_world_pos():
        s = State.camera.world_to_screen(State.camera.position)
        w = State.camera.position
        return 'S'+str((int(s.x),int(s.y),)) + ' W'+str((int(w.x),int(w.y),))
    State.hud.add('Camera',
        Statf(next_pos(), 'Camera %s', callback=get_world_pos, interval=100))

    def gui_name():
        w = State.app.gui_hover()
        return w.name if w else 'None'
    State.hud.add('Widget',
        Statf(next_pos(), 'Widget %s', callback=gui_name, interval=100))
    
    def get_selected():
        shape = State.app.selected
        return 'None' if shape is None else '%s@%s'%(
            shape.rect.center, State.world.level_of(shape))
    State.hud.add('Selected',
        Statf(next_pos(), 'Selected %s', callback=get_selected, interval=100))
    
# make_hud


def make_menus(app):
    menus = gui.Menus([
        ('File/New', app.new_map, None),
        ('File/Open', app.open_map, None),
        ('File/Save', app.save_map, None),
        ('File/Save As', app.save_as_map, None),
        ('File/Quit', app.quit_app, None),
        ('View/Grid', app.toggle_grid, None),
        ('View/Labels', app.toggle_labels, None),
        ('View/HUD', app.toggle_hud, None),
    ], name='menus')
    return menus
    
# make_menus


def make_toolbar(app):
    g = gui.Group(name='toolbar', value='rect_tool')
    h = app.menus.rect.height
    t = gui.Table()
    t.tr()
    t.td(gui.Tool(g, gui.Label('Rect'), 'rect_tool', height=h))
    t.td(gui.Tool(g, gui.Label('Triangle'), 'triangle_tool', height=h))
    t.td(gui.Tool(g, gui.Label('Quad'), 'quad_tool', height=h))
    t.td(gui.Tool(g, gui.Label('Poly'), 'poly_tool', height=h))
    t.td(gui.Tool(g, gui.Label('Circle'), 'circle_tool', height=h))
    return g,t
    
# make_toolbar


def main():
    map_editor = MapEditor()
    map_editor.run()


if __name__ == '__main__':
    if True:
        main()
    else:
        cProfile.run('main()', 'prof.dat')
        p = pstats.Stats('prof.dat')
        p.sort_stats('time').print_stats()
