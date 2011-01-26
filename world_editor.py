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

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

NOTE: Limited saving and loading now exist. This is very basic and *will* change
over time as features are added to the world file format. However, it is all
ASCII so it should be pretty easy to script a quick-n-dirty converter.

* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

Controls:
    * Menus do what you'd expect.
    * Scrollbars do what you'd expect.
    * Toolbar selects a shape to insert into the map.
    * Right-click: inserts a shape into the map.
    * Left-click:
        * Clicking inside a shape selects that shape for further manipulation.
        * Clicking outside a shape deselects the selected shape.
        * Clicking inside stacked shapes selects the next shape.
        * Clicking and dragging the center control point moves the shape.
        * Clicking and dragging a corner control point reshapes a shape.

Design:
    There will likely be a form in the space on the right. Selecting a shape
    will allow data from the form to be attached to it, and data already
    attached will be displayed in the form. The world file loader can then use
    that data for any robust purpose.
    
    Below the form in the space on the right will be a tile palette. This is
    for decorating the map so that one can see the graphics for spawned and/or
    collidable objects while sizing their shapes in the world.
    
    It is undecided at this time if the shape-graphics association will be
    saved with the world map format. On the one hand it can ease map creation.
    On the other hand it may greatly complicate parsing world maps. Maybe an
    editor extension in secondary files is the answer: then game map loaders can
    choose to use or ignore the association data in secondary files.
    
    Beyond the essentials, there is also an unwritten wish list of features
    which may get added as demand dictates and time permits.
"""


## Python
import cProfile
import pstats
import os
from os.path import join as joinpath, normpath
import sys
import time
import traceback

## pygame
import pygame
from pygame.locals import *

## Gummworld2
import paths
from gamelib import (
    model, data, geometry, toolkit,
    State, Camera, Map, Screen, View,
    HUD, Stat, Statf,
    GameClock, Vec2d,
)
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


class TimeThing(object):
    
    strftime = time.strftime
    
    def __init__(self, fmt):
        self.fmt = fmt
    
    def __str__(self):
        ms = time.time() % 1
        return self.strftime(self.fmt) + ('%.3f' % ms).lstrip('0')


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
        # Indicate mouse-over.
        if self in app.mouseover_shapes:
            color = Color('white')
        else:
            color = Color('grey')
        # Draw rect in screen space.
        r = self.rect.copy()
        r.center = world_to_screen(self.rect.center)
        self.draw_rect(surface, color, r, 1)
        # If shape is selected, draw control points in screen space.
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
            # Poly point grabbed. Recalculate rect in world space.
            controls = controls[:-1]
            xvals = [c.centerx for c in controls]
            yvals = [c.centery for c in controls]
            xmin = reduce(min, xvals)
            width = reduce(max, xvals) - xmin + 1
            ymin = reduce(min, yvals)
            height = reduce(max, yvals) - ymin + 1
            self.rect.topleft = xmin,ymin
            self.rect.size = width,height
            
            # Recalculate points in local space relative to rect.
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
        # Indicate mouse-over.
        if self in app.mouseover_shapes:
            color = Color('white')
        else:
            color = Color('grey')
        # Draw rect in screen space.
        if State.show_rects:
            r = self.rect.copy()
            r.center = world_to_screen(self.rect.center)
            self.draw_rect(surface, Color('grey'), r, 1)
        # Draw poly points in screen space.
        pos = world_to_screen(self.rect.topleft)
        points = [p+pos for p in self._points]
        self.draw_poly(surface, color, points, 1)
        # If shape is selected, draw control points in screen space.
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
        # Indicate mouse-over.
        if self in app.mouseover_shapes:
            color = Color('white')
        else:
            color = Color('grey')
        # Draw rect in screen space.
        if State.show_rects:
            r = self.rect.copy()
            r.center = world_to_screen(self.rect.center)
            self.draw_rect(surface, Color('grey'), r, 1)
        # Draw circle in screen space.
        self.draw_circle(surface, color,
            world_to_screen(self.origin), self.radius, 1)
        # If shape is selected, draw control points in screen space.
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
        screen_size = Vec2d(800,600)
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
        State.clock = GameClock(30, 30)
        State.camera.position = State.camera.view.center
        pygame.display.set_caption('Gummworld2 World Editor')
        
        # Mouse details.
        #   mouse_shape: world entity for mouse interaction.
        #   mouse_down: mouse button currently held down.
        #   selected: world entity currently selected.
        #   mouseover_shapes: list of shapes over which the mouse is hovering.
        self.mouse_shape = RectGeom(0,0,5,5)
        self.mouse_down = 0
        self.selected = None
        self.mouseover_shapes = []
        
        # Event loop idle control. Makes app play nicer when not in use, more
        # responsive when in use.
        self.idle = 0
        self.time = TimeThing('%M%S')
        
        # Gooey stuff.
        self.make_gui()
        self.modal = None
        self.changes_unsaved = False
        
        # Make some default content and HUD.
        toolkit.make_tiles2()
        make_hud()
        State.show_hud = True
        State.show_grid = True
        State.show_labels = True
        State.show_rects = False
        
        # Files.
        State.file_entities = None
        State.file_map = None
        
    # MapEditor.__init__
    
    def run(self):
        """The run loop.
        """
        State.running = True
        while State.running:
            # Ticks and frame rate are not independent here.
            State.clock.tick()
            self.get_events()
            self.update()
            self.draw()
    
    def update(self):
        """Update all.
        """
        # Update stuff.
        self.update_gui()
        State.camera.update()
        self.update_shapes()
        if State.show_hud:
            State.hud.update()
    
    def update_gui(self):
        """Update the GUI, then update the app from the GUI.
        """
        # Plucked from gui.App.loop().
        gui = self.gui
        gui.set_global_app()
        gui.update()
        State.camera.position = self.h_map_slider.value,self.v_map_slider.value
    
    def update_shapes(self):
        """Update the mouseover_shapes list.
        """
        mouse_shape = self.mouse_shape
        self.mouseover_shapes = [shape for ent,shape in State.world.collisions
            if ent is mouse_shape
        ]
    
    def draw(self):
        """Draw all.
        """
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
    
    def draw_world(self):
        """Draw the on-screen shapes in the world.
        """
        mouse_shape = self.mouse_shape
        things = State.world.entities_in(State.camera.rect)
        for thing in things:
            if thing is not mouse_shape:
                thing.draw()
    
    def deselect(self):
        """Deselect a shape and release its "grabbed" control point.
        """
        if self.selected:
            self.selected.release()
            self.selected = None
    
    def make_gui(self):
        """Make the entire GUI.
        """
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
    
    def make_scrollbars(self, c, reset=True):
        """Make map scrollbars to fit the window.
        """
        view_rect = State.camera.view.parent_rect
        w,h = view_rect.size
        thick = 15
        
        #   H-slider.
        minv = view_rect.centerx - thick
        maxv = State.map.tile_size.x * State.map.map_size.x - minv + thick
        size = max(round(float(w) / State.map.rect.w * w), 25)
        if reset:
            val = view_rect.centerx
        else:
            val = self.h_map_slider.value
        #   val, min, max, len-px, step
        self.h_map_slider = gui.HSlider(val,minv,maxv,size,
            name='h_map_slider', width=w-thick, height=thick)
        self.h_map_slider.rect.bottomleft = view_rect.bottomleft
        c.add(self.h_map_slider, *self.h_map_slider.rect.topleft)
        
        #   V-slider.
        minv = view_rect.centery - self.menus.rect.bottom - 3
        maxv = State.map.tile_size.y * State.map.map_size.y - minv + thick
        size = max(round(float(h) / State.map.rect.h * h), 25)
        if reset:
            val = view_rect.centery
        else:
            val = self.v_map_slider.value
        #   val, min, max, len-px, step
        self.v_map_slider = gui.VSlider(val,minv,maxv,size,
            name='v_map_slider', height=h-thick, width=thick)
        self.v_map_slider.rect.topright = view_rect.topright
        c.add(self.v_map_slider, *self.v_map_slider.rect.topleft)
        
    # MapEditor.make_sliders
    
    def remake_scrollbars(self, reset=True):
        """Remake the map scrollbars after video-resize event or a map load.
        """
        c = self.gui.widget
        c.remove(self.h_map_slider)
        c.remove(self.v_map_slider)
        self.make_scrollbars(c, reset)
    
    def gui_hover(self):
        """Return True if the mouse is hovering over a GUI widget.
        """
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
    
    def gui_confirm_discard(self, callback, ok=True, cancel=False):
        """Confirm discard dialog: Ok or Cancel.
        """
        def set_value(dialog, value):
            dialog.value = value
            dialog.close()
        def modal_off(*args):
            State.app.modal = None
        
        content = gui.Table()
        d = gui.Dialog(gui.Label('Gummworld2 World Editor'), content)
        d.value = cancel
        
        button_ok = gui.Button('Ok')
        button_ok.connect(gui.CLICK, set_value, d, ok)
        button_cancel = gui.Button('Cancel')
        button_cancel.connect(gui.CLICK, set_value, d, cancel)
        
        content.tr()
        content.td(gui.Label('Changes will be lost.'), colspan=2)
        content.tr()
        content.td(button_ok, align=0)
        content.td(button_cancel, align=0)
        
        d.connect(gui.CLOSE, modal_off, None)
        d.connect(gui.CLOSE, callback, 'check_discard', d)
        d.open()
        self.modal = d
        
    # MapEditor.gui_confirm_discard
    
    def gui_alert(self, message):
        """Simple popup message dialog.
        """
        def modal_off(*args):
            State.app.modal = None
        button = gui.Button('Ok')
        d = gui.Dialog(gui.Label(message), button)
        button.connect(gui.CLICK, d.close, None)
        d.connect(gui.CLOSE, modal_off, None)
        d.open()
        self.modal = d
    
    def gui_browse_file(self, title, path, callback):
        """Dialog to browse for a file.
        """
        def modal_off(*args):
            State.app.modal = None
        d = gui.FileDialog(title_txt="Import Entities", path=data.path['map'])
        d.connect(gui.CLOSE, modal_off, None)
        d.connect(gui.CLOSE, callback, 'file_picked', d)
        d.open()
        self.modal = d
    
    def action_mouse_click(self, e):
        """Mouse click action: button 3 inserts a shape; button 1 selects,
        deselects or sizes a shape.
        """
        if self.modal is not None:
            return
        elif self.mouse_down == 3:
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
            self.changes_unsaved = True
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
        """Mouse drag event (mouse is held down): button 3 moves a shape if the
        button is still held down after insert; button 1 moves or sizes a shape.
        """
        if self.selected:
            if self.mouse_down == 3:
                # Move the selected shape.
                self.selected.position = State.camera.screen_to_world(e.pos)
                State.world.add(self.selected)
                self.changes_unsaved = True
            elif self.mouse_down == 1:
                # Resize the selected shape.
                grabbed = self.selected.grabbed
                if grabbed is not None:
                    grabbed.position = State.camera.screen_to_world(e.pos)
                    State.world.add(grabbed.parent)
                    self.changes_unsaved = True
        
    # MapEditor.action_mouse_drag

    def action_mouse_release(self, e):
        """Mouse release action: release the selected shape's control point.
        """
        if self.selected:
            self.selected.release()
    
    def action_map_new(self, *args):
        """New map action: create a new map with default content.
        """
        # Get map dimensions.
        ######################################
        ## Needs a form to get map dimensions.
        ######################################
        State.map.clear()
        toolkit.make_tiles2()
        self.remake_scrollbars()
        State.file_map = None
        
    # MapEditor.action_map_new
    
    def action_map_open(self, sub_action=None, widget=None):
        """Import map action: loads a map from file (currently Tiled TMX only).
        """
        if sub_action is None:
            # Get input file name.
            self.gui_browse_file("Import Map",
                data.path['map'], self.action_map_open)
        elif sub_action == 'file_picked':
            d = widget
            if d.value is not None:
                State.file_map = d.value
                # Import map.
                if State.file_map.endswith('.tmx'):
                    try:
                        State.map = toolkit.load_tiled_tmx_map(State.file_map)
                    except:
                        self.gui_alert('Failed to import map')
                        traceback.print_exc()
                self.remake_scrollbars()
            State.screen.clear()
        
    # MapEditor.action_map_open
    
    def action_entities_new(self, sub_action=None, widget=None):
        """New entities action: clear all entities from editor.
        """
        if sub_action is None:
            # If changed, confirm discard.
            if self.changes_unsaved:
                self.gui_confirm_discard(self.action_entities_new)
            else:
                self.action_entities_new('check_discard')
        elif sub_action == 'check_discard':
            if widget is None or widget.value is True:
                # Clear out the world.
                State.world.remove(*State.world.entity_branch.keys())
                State.file_entities = None
        
    # MapEditor.action_entities_new
    
    def action_entities_open(self, sub_action=None, widget=None):
        """Import entities action: load entities from a file.
        """
        if sub_action is None:
            # If changed, confirm discard.
            if self.changes_unsaved:
                self.gui_confirm_discard(self.action_entities_open)
            else:
                self.action_entities_open('check_discard')
        elif sub_action == 'check_discard':
            if widget is None or widget.value is True:
                # Get input file name.
                self.gui_browse_file("Import Entities",
                    data.path['map'], self.action_entities_open)
        elif sub_action == 'file_picked':
            d = widget
            if d.value is not None:
                State.file_entities = d.value
                # Specify the importer plugin to use.
                import_script = data.filepath(
                    'plugins', joinpath('map','import_world_quadtree.py'))
                # Clear out the world.
                State.world.remove(*State.world.entity_branch.keys())
                # Run the importer plugin.
                try:
                    file_handle = open(State.file_entities, 'rb')
                    locals_dict = {
                        'fh'         : file_handle,
                        'rect_cls'   : RectGeom,
                        'poly_cls'   : PolyGeom,
                        'circle_cls' : CircleGeom,
                    }
                    execfile(import_script, {}, locals_dict)
                    self.changes_unsaved = False
                except:
                    self.gui_alert('Failed to import world')
                    traceback.print_exc()
                else:
                    file_handle.close()
                    # Add the entities to the world.
                    entities = locals_dict['entities']
                    State.world.add(*entities)
                # Put the mouse shape back.
                State.world.add(self.mouse_shape)
        State.screen.clear()
        
    # MapEditor.action_entities_open
    
    def action_entities_save(self, *args):
        """Save entities action: save entities to a file.
        """
        # Make sure a save file has been named.
        if State.file_entities is None:
            self.action_entities_save_as()
            if State.file_entities is None:
                return
        # Specify the exporter plugin to use.
        export_script = data.filepath(
            'plugins', joinpath('map','export_world_quadtree.py'))
        # Don't save the mouse shape.
        State.world.remove(self.mouse_shape)
        # Run the exporter plugin.
        try:
            file_handle = open(State.file_entities, 'wb')
            locals_dict = {
                'entities' : State.world.entity_branch.keys(),
                'fh' : file_handle,
            }
            execfile(export_script, {}, locals_dict)
            self.changes_unsaved = True
        except:
            traceback.print_exc()
        else:
            file_handle.close()
        # Put the mouse shape back.
        State.world.add(self.mouse_shape)
        
    # MapEditor.action_entities_save
    
    def action_entities_save_as(self, sub_action=None, widget=None):
        """Save-as entities action: save entities to a file, selecting a new
        file name.
        """
        if sub_action is None:
            # Get input file name.
            self.gui_browse_file("Save Entities",
                data.path['map'], self.action_entities_save_as)
        elif sub_action == 'file_picked':
            d = widget
            if d.value is not None:
                State.file_entities = d.value
                self.action_entities_save()
        State.screen.clear()
    
    def action_quit_app(self, sub_action=None, widget=None):
        """Quit app action.
        """
        if sub_action is None:
            # If changed, confirm discard.
            if self.changes_unsaved:
                self.gui_confirm_discard(self.action_quit_app)
            else:
                self.action_quit_app('check_discard')
        elif sub_action == 'check_discard':
            if widget is None or widget.value is True:
                quit()
    
    def action_view_grid(self, *args):
        """View grid action: toggle.
        """
        State.show_grid = not State.show_grid
    
    def action_view_labels(self, *args):
        """View labels action: toggle labels.
        """
        State.show_labels = not State.show_labels
    
    def action_view_rects(self, *args):
        """View rects action: toggle rects.
        """
        State.show_rects = not State.show_rects
    
    def action_view_hud(self, *args):
        """View HUD action: toggle HUD.
        """
        State.show_hud = not State.show_hud
    
    def get_events(self):
        """Get and dispatch events with nicest idle-wait.
        """
        events = [pygame.event.wait()]
        events.extend(pygame.event.get())
        for e in events:
            typ = e.type
            if typ == KEYDOWN:
                self.on_key_down(e, e.unicode, e.key, e.mod)
            elif typ == KEYUP:
                self.on_key_up(e, e.key, e.mod)
            elif typ == MOUSEMOTION:
                self.on_mouse_motion(e, e.pos, e.rel, e.buttons)
            elif typ == MOUSEBUTTONUP:
                self.on_mouse_button_up(e, e.pos, e.button)
            elif typ == MOUSEBUTTONDOWN:
                self.on_mouse_button_down(e, e.pos, e.button)
            elif typ == VIDEORESIZE:
                self.on_resize(e, e.size, e.w, e.h)
            elif typ == USEREVENT:
                self.on_user_event(e)
            elif typ == QUIT:
                    self.on_quit()
        
    # MapEditor.get_events
    
    def on_key_down(self, e, unicode, key, mod):
        """Handler for KEYDOWN events.
        """
        # Maybe some accelerator keys or something.
        self.gui.event(e)
        ## Customization: beware of key conflicts with pgu.gui.
        if not self.modal:
            if key in (K_DELETE,K_KP_PERIOD):
                if self.selected is not None:
                    shape = self.selected 
                    self.deselect()
                    State.world.remove(shape)
            elif key == K_ESCAPE:
                self.action_quit_app()
#            else:
#                print 'Key down', pygame.key.name(key)
    
    def on_key_up(self, e, key, mod):
        """Handler for KEYUP events.
        """
        # Maybe some accelerator keys or something.
        self.gui.event(e)
    
    def on_mouse_button_down(self, e, pos, button):
        """Handler for MOUSEBUTTONDOWN events.
        """
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
    
    def on_mouse_motion(self, e, pos, rel, buttons):
        """Handler for MOUSEMOTION events.
        """
        self.mouse_shape.position = State.camera.screen_to_world(pos)
        State.world.add(self.mouse_shape)
        if not self.mouse_down:
            self.gui.event(e)
        else:
            # Crossing GUI widgets does not interfere with dragging.
            self.action_mouse_drag(e)
    
    def on_mouse_button_up(self, e, pos, button):
        """Handler for MOUSEBUTTONUP events.
        """
        self.gui.event(e)
        if self.mouse_down:
            # Crossing GUI widgets does not interfere with drag-and-release.
            if self.mouse_down == button:
                self.action_mouse_release(e)
                self.mouse_down = 0
    
    def on_resize(self, e, screen_size, w, h):
        """Handler for VIDEORESIZE events.
        """
        # Update the pygame display mode and Gummworld2 camera view.
        width,height = w,h
        State.screen = Screen(screen_size, RESIZABLE)
        State.camera.view = View(State.screen.surface, Rect(0,0,w*2/3,h))
        
        # Resize the widgets.
        self.gui.widget.resize(width=w, height=h)
        self.remake_scrollbars(reset=False)
    
    def on_user_event(self, e):
        """Handler for USEREVENT events.
        """
#        print 'USEREVENT',e.dict()
        pass
    
    def on_quit(self):
        """Handler for QUIT events.
        """
        self.action_quit_app()


def make_hud():
    """Create a HUD with dynamic items.
    """
    State.hud = HUD()
    State.hud.x += 20
    State.hud.i += 3
    next_pos = State.hud.next_pos
    
#    State.hud.add('FPS',
#        Statf(next_pos(), 'FPS %d', callback=State.clock.get_fps))
    
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
    """Make GUI menus for content control.
    """
    menus = gui.Menus([
        ('File/Quit',        app.action_quit_app, None),
        ('Entities/New',     app.action_entities_new, None),
        ('Entities/Open',    app.action_entities_open, None),
        ('Entities/Save',    app.action_entities_save, None),
        ('Entities/Save As', app.action_entities_save_as, None),
        ('Map/New',          app.action_map_new, None),
        ('Map/Open',         app.action_map_open, None),
        ('View/Grid',        app.action_view_grid, None),
        ('View/Labels',      app.action_view_labels, None),
        ('View/Rects',       app.action_view_rects, None),
        ('View/HUD',         app.action_view_hud, None),
    ], name='menus')
    return menus
    
# make_menus


def make_toolbar(app):
    """Make GUI toolbar with shape tools in it.
    """
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
    """Da main... uh... thing.
    """
    map_editor = MapEditor()
    map_editor.run()


if __name__ == '__main__':
    if True:
        main()
    else:
        cProfile.run('main()', 'prof.dat')
        p = pstats.Stats('prof.dat')
        p.sort_stats('time').print_stats()