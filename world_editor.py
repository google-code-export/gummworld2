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
    *   Menus do what you'd expect.
    *   Scrollbars do what you'd expect.
    *   Toolbar selects a shape to insert into the map.
    *   Right-click: inserts a shape into the map.
    *   Left-click:
        *   Clicking inside a shape selects that shape for further manipulation.
        *   Clicking outside a shape deselects the selected shape.
        *   Clicking inside stacked shapes selects the next shape.
        *   Clicking and dragging the center control point moves the shape.
        *   Clicking and dragging a corner control point reshapes a shape.

Design:
    There is a form in the space on the right. Selecting a shape
    will allow data from the form to be attached to it, and data already
    attached will be displayed in the form. The world file loader can then use
    that data for any robust purpose.
    
    Below the form in the space on the right is a tile palette. This is
    for decorating the map so that one can see the graphics for spawned and/or
    collidable objects while sizing their shapes in the world.
    
    It is undecided at this time if the shape-graphics association will be
    saved with the world map format. On the one hand it can ease map creation.
    On the other hand it may greatly complicate parsing world maps. Maybe an
    editor extension in secondary files is the answer: then game map loaders can
    choose to use or ignore the association data in secondary files.
    
    Beyond the essentials, there is also an unwritten wish list of features
    which may get added as demand dictates and time permits.

Bugs:
    *   

Basic to do (complete for 1.0 release):
    *   action_map_new() needs a Size Form.
    *   Form for picking images.
    *   Images attached to world shapes.
    *   [DONE] Form for user_data.
        *   Option to add image path to user_data.
    *   Single operations: Cut, copy, paste?
    *   Undo, redo.
    *   Contrast aid: Cycle through color schemes for world shapes.
    *   Chooser: Importer and exporter (e.g., ASCII, pickle, custom).
    *   Help viewer? PGU makes it easy.

Advanced to do:
    *   Productivity:
        *   Shape templates: Make a shape, add to template list. Choose from
            list to insert "cookie cut" shapes.
        *   User_data templates: a la Shape templates.
        *   Group operations: Delete, move; cut, copy, paste?
    *   Proof-reading:
        *   List unique user_data and count. Click list item to go to shapes.
    *   Clicking on map while dragging scrollbar inserts a shape. Probably
        should sense when GUI is clicked/dragged and not do editor actions. Not
        important, but it is kind of sloppy.
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
    model, data, geometry, toolkit, pygame_utils,
    State, Camera, Map, Screen, View,
    HUD, Stat, Statf,
    GameClock, Vec2d,
)
import gui


# Filename-matching extensions for image formats that pygame can load.
IMAGE_FILE_EXTENSIONS = (
    'gif','png','jpg','jpeg','bmp','pcx', 'tga', 'tif',
    'lbm', 'pbm', 'pgm', 'xpm',
)

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
    """Calling str() on instances of this class return a formatted time string
    with thousanths of a second appended (e.g. 10:15:59.999).
    
    Pass a strftime() format string to the constructor, or assign such a format
    string to the fmt instance variable.
    """
    
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
    
    typ = 'Rect'
    draw_rect = pygame.draw.rect
    
    def __init__(self, *args, **kw):
        super(RectGeom, self).__init__(*args, **kw)
        self._attrs = 'topleft','topright','bottomright','bottomleft','center'
        self._cp = [ControlPoint(self, self._attrs[i]) for i in range(5)]
        self.grabbed = None
        self.user_data = ''
        
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
        # Update shape's position.
        p = self._position
        p.x,p.y = self.rect.center
        
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
    
    typ = 'Poly'
    draw_poly = pygame.draw.polygon
    draw_rect = pygame.draw.rect
    
    def __init__(self, *args, **kw):
        super(PolyGeom, self).__init__(*args, **kw)
        
        self._points = [Vec2d(p) for p in self._points]
        
        self.tmp_rect = self.rect.copy()
        self._cp = [ControlPoint(self, i) for i in range(len(self._points)+1)]
        self._cp = self.control_points
        self.grabbed = None
        self.user_data = ''
        
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
    
    typ = 'Circle'
    draw_circle = pygame.draw.circle
    draw_rect = pygame.draw.rect
    
    def __init__(self, *args, **kw):
        super(CircleGeom, self).__init__(*args, **kw)
        self._attrs = 'origin','radius'
        self._cp = [ControlPoint(self, self._attrs[i]) for i in range(2)]
        self.grabbed = None
        self.user_data = ''
        
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
            model.QuadTreeObject(Rect(0,0,5,5)),
            View(State.screen.surface, Rect(0,0,screen_size.x*2/3,screen_size.y))
        )
        State.world = model.WorldQuadTree(
            State.map.rect, worst_case=99, collide_entities=True)
        State.clock = GameClock(30, 30)
        State.camera.position = State.camera.view.center
        pygame.display.set_caption('Gummworld2 World Editor')
        x,y = State.camera.view.rect.topleft
        w,h = Vec2d(screen_size) - (State.camera.view.rect.right,0)
        State.gui_panel = View(State.screen.surface, Rect(x,y,w,h))
        State.screen.eraser.fill(Color('grey'))
        
        # Mouse details.
        #   mouse_shape: world entity for mouse interaction.
        #   mouse_down: mouse button currently held down.
        #   selected: world entity currently selected.
        #   mouseover_shapes: list of shapes over which the mouse is hovering.
        self.mouse_shape = RectGeom(0,0,5,5)
        self.mouse_down = 0
        self.selected = None
        self.mouseover_shapes = []
        
        # Some things to aid debugging.
        self.time = TimeThing('%M%S')
        self.verbose = False
        
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
        if self.verbose:
            print self.time,State.world.collisions
    
    def draw(self):
        """Draw all.
        """
        # Draw stuff.
        State.camera.interpolate()
        State.screen.clear()
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
    
    def select(self, shape):
        self.selected = shape
        # Update shape info form.
        self.gui_form['shape_type'].set_text(self.selected.typ)
        self.gui_form['shape_pos'].set_text(str(tuple(self.selected.position)))
        self.gui_form['user_data'].value = self.selected.user_data
    
    def deselect(self):
        """Deselect a shape and release its "grabbed" control point.
        """
        if self.selected:
            self.selected.release()
            self.selected = None
            self.gui_form['shape_type'].set_text('no selection')
            self.gui_form['shape_pos'].set_text('')
            self.gui_form['user_data'].value = ''
            self.gui_form['user_data'].blur()
    
    def make_gui(self):
        """Make the entire GUI.
        """
        # Make the GUI, a form, and a container.
        self.gui = gui.App(theme=gui.Theme(dirs=['data/themes/default']))
        self.gui_form = gui.Form()
        width,height = State.screen.size
        c = gui.Container(width=width,height=height)
        
        # Menus.
        make_menus(c)
        # Toolbar.
        make_toolbar(c)
        # Scrollbars for scrolling map.
        self.make_scrollbars(c)
        # Shape-info form.
        make_side_panel(c)
        
        # Gogogo GUI.
        self.gui.init(widget=c, screen=State.screen.surface)
        
        # This forces the gui.Form to update its internals.
        self.gui_form['toolbar']
        
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
        minv = view_rect.centery - self.gui_form['menus'].rect.bottom - 3
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
    
    def gui_modal_off(self, *args):
        State.app.modal = None
    
    def gui_hover(self):
        """Return True if the mouse is hovering over a GUI widget.
        """
        # I know accessing _attrs frowned upon, but gui.Form doesn't work right.
        for name,widget in self.gui_form._emap.items():
            if widget.is_hovering():
                return widget
        for menu in self.gui_form['menus'].widgets:
            if menu.options.is_open():
                return menu.options
        return None
        
    # MapEditor.gui_hover
    
    def gui_confirm_discard(self, callback, ok=True, cancel=False):
        """Confirm discard dialog: Ok or Cancel.
        """
        def set_value(dialog, value):
            dialog.value = value
            dialog.close()
        
        content = gui.Table()
        d = gui.Dialog(gui.Label('Gummworld2 World Editor'), content, name='modal')
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
        
        d.connect(gui.CLOSE, self.gui_modal_off, None)
        d.connect(gui.CLOSE, callback, 'check_discard', d)
        d.open()
        self.modal = d
        
    # MapEditor.gui_confirm_discard
    
    def gui_alert(self, message):
        """Simple popup message dialog.
        """
        button = gui.Button('Ok')
        d = gui.Dialog(gui.Label(message), button)
        button.connect(gui.CLICK, d.close, None)
        d.connect(gui.CLOSE, self.gui_modal_off, None)
        d.open()
        self.modal = d
    
    def gui_view_text(self, title, lines, width=400, height=200):
        """A text viewer suitable for viewing plain text verbatim. lines is a
        list of strings. Strings are split on '\n', and '\r' is stripped. Text
        is left-justified. No paragraph spacing is inserted.
        """
        
        title = gui.Label(title)
        doc = gui.Document(width=width)
        
        space = title.style.font.size(' ')
        
        for line in lines:
            line = line.strip('\r')
            line = line.rstrip('\n')
            doc.block(align=-1)
            for line in line.split('\n'):
                for word in line.split(' '):
                    if len(word):
                        doc.add(gui.Label(word))
                    doc.space(space)
                doc.br(1)
        
        self.modal = gui.Dialog(title, gui.ScrollArea(doc,width+20,height))
        self.modal.connect(gui.CLOSE, self.gui_modal_off, None)
        self.modal.open()
    
    def gui_view_doc(self, title, lines, width=400, height=200):
        """A text viewer suitable for viewing prose. lines is a list of strings.
        Each string is a paragraph. Text is centered. Paragraph spacing is
        inserted between lines.
        """
        title = gui.Label(title)
        doc = gui.Document(width=width)
        
        space = title.style.font.size(' ')
        
        for line in lines:
            line = line.rstrip('\r\n')
            doc.block(align=0)
            for word in line.split(' '):
                doc.add(gui.Label(word))
                doc.space(space)
            doc.br(space[1])
        
        self.modal = gui.Dialog(title, gui.ScrollArea(doc,width+20,height))
        self.modal.connect(gui.CLOSE, self.gui_modal_off, None)
        self.modal.open()
    
    def gui_browse_file(self, title, path, callback):
        """Dialog to browse for a file.
        """
        d = gui.FileDialog(title_txt=title, path=path)
        d.connect(gui.CLOSE, self.gui_modal_off, None)
        d.connect(gui.CLOSE, callback, 'file_picked', d)
        d.open()
        self.modal = d
    
    def gui_tile_sheet_sizer(self, file_path, callback):
#        try:
#            image,rect = pygame_utils.load_image(file_path)
#        except:
#            exc_type,exc_value,exc_traceback = sys.exc_info()
#            self.gui_view_text('Load tile sheet failed',
#                traceback.format_exception(exc_type, exc_value, exc_traceback),
#                width=640, height=480)
#            traceback.print_exc()
#            return
        def do_click(*args):
            print 'CLICK args:',args
            pass
        # Tile sheet dimensions.
        t = gui.Table()
        t.tr()
        t.td(gui.Label('Width:'))
        t.td(gui.Label('0', name='tile_width'), align=-1)
        t.tr()
        t.td(gui.Label('Height:'))
        t.td(gui.Label('0', name='tile_height'), align=-1)
        t.tr()
        t.td(gui.Label('Margin:'))
        t.td(gui.Label('0', name='tile_margin'), align=-1)
        t.tr()
        t.td(gui.Label('Spacing:'))
        t.td(gui.Label('0', name='tile_spacing'), align=-1)
        
        # Sizer gadgets.
        t.tr()
        image = gui.Image(file_path)
        s = gui.ScrollArea(image, 320, 200)
        t.td(s, colspan=2)
        d = gui.Dialog(gui.Label('Tile Sheet Sizer'), t)
        d.value = None
        d.connect(gui.CLOSE, self.gui_modal_off, None)
        d.connect(gui.CLOSE, callback, 'file_picked', d)
        d.connect(gui.CLICK, do_click, d)
        # Buttons: Ok, Cancel
        d.open()
        self.modal = d
    
    # MapEditor.gui_tile_sheet_sizer
    
    def action_set_userdata(self, user_data):
        """GUI input field changed, set the selected shape's user_data.
        """
        if self.selected is not None:
            self.selected.user_data = user_data.value
            self.changes_unsaved = True
    
    def action_mouse_click(self, e):
        """Mouse click action: button 3 inserts a shape; button 1 selects,
        deselects or sizes a shape.
        """
        if not self.mouse_shape.rect.colliderect(State.camera.view.rect):
            # Don't change the map if clicking outside the map area.
            return
        elif self.modal is not None:
            # Don't change the map if a modal dialog is open.
            return
        elif self.mouse_down == 3:
            # Right-click: Put a shape.
            pos = State.camera.screen_to_world(e.pos)
            shape = self.gui_form['toolbar_group'].value
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
            self.select(geom)
            State.world.add(geom)
            self.changes_unsaved = True
        elif self.mouse_down == 1:
            # Left-click: Select, deselect, or grab.
            mouseover_shapes = self.mouseover_shapes
            if self.selected not in mouseover_shapes:
                self.deselect()
                if len(mouseover_shapes):
                    self.select(mouseover_shapes[0])
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
                    self.select(mouseover_shapes[i])
        
    # MapEditor.action_mouse_click

    def action_mouse_drag(self, e):
        """Mouse drag event (mouse is held down): button 3 moves a shape if the
        button is still held down after insert; button 1 moves or sizes a shape.
        """
        selected = self.selected
        if selected:
            if self.mouse_down == 3:
                # Move the selected shape.
                selected.position = State.camera.screen_to_world(e.pos)
                State.world.add(selected)
                self.changes_unsaved = True
            elif self.mouse_down == 1:
                # Resize the selected shape.
                grabbed = selected.grabbed
                if grabbed is not None:
                    grabbed.position = State.camera.screen_to_world(e.pos)
                    State.world.add(selected)
                    self.changes_unsaved = True
            self.gui_form['shape_pos'].set_text(str(tuple(selected.position)))
        
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
    
    def action_map_load(self, sub_action=None, widget=None):
        """Load map action: loads a map from file (currently Tiled TMX only).
        """
        if sub_action is None:
            # Get input file name.
            self.gui_browse_file("Import Map",
                data.path['map'], self.action_map_load)
        elif sub_action == 'file_picked':
            d = widget
            if d.value is not None:
                State.file_map = d.value
                # Import map.
                if State.file_map.endswith('.tmx'):
                    try:
                        State.map = toolkit.load_tiled_tmx_map(State.file_map)
                    except:
                        exc_type,exc_value,exc_traceback = sys.exc_info()
                        self.gui_view_text('Load map failed',
                            traceback.format_exception(
                                exc_type, exc_value, exc_traceback),
                            width=640, height=480)
                        traceback.print_exc()
                self.remake_scrollbars()
        
    # MapEditor.action_map_load
    
    def action_tiles_load(self, sub_action=None, widget=None):
        if sub_action is None:
            # Get input file name.
            self.gui_browse_file('Import Tiles',
                data.path['image'], self.action_tiles_load)
        elif sub_action == 'file_picked':
            ## Do something with the file.
            d = widget
            if d.value is not None:
                file_path = d.value
                # Make sure we have a file.
                if not os.path.isfile(file_path):
                    self.gui_alert('Not a file: '+file_path)
                    return
                ext = os.path.splitext(file_path)[1][1:]
                # Make sure we have an image file type (check extension).
                if ext.lower() not in IMAGE_FILE_EXTENSIONS:
                    self.gui_alert('Unsupported image file type: '+ext)
                    return
                # Hand off to the sizer dialog.
                try:
                    self.gui_tile_sheet_sizer(file_path, self.action_tiles_load)
                except:
                    pass
        elif sub_action == 'tile_sheet_sized':
            pass

    # MapEditor.action_tiles_load
    
    def action_entities_clear(self, sub_action=None, widget=None):
        """Clear entities action: clear all entities from editor.
        """
        if sub_action is None:
            # If changed, confirm discard.
            if self.changes_unsaved:
                self.gui_confirm_discard(self.action_entities_clear)
            else:
                self.action_entities_clear('check_discard')
        elif sub_action == 'check_discard':
            if widget is None or widget.value is True:
                # Clear out the world.
                State.world.remove(*State.world.entity_branch.keys())
                State.file_entities = None
                self.changes_unsaved = False
        
    # MapEditor.action_entities_clear
    
    def action_entities_import(self, sub_action=None, widget=None):
        """Import entities action: load entities from a file.
        """
        if sub_action is None:
            # If changed, confirm discard.
            if self.changes_unsaved:
                self.gui_confirm_discard(self.action_entities_import)
            else:
                self.action_entities_import('check_discard')
        elif sub_action == 'check_discard':
            if widget is None or widget.value is True:
                # Get input file name.
                self.gui_browse_file("Import Entities",
                    data.path['map'], self.action_entities_import)
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
                    exc_type,exc_value,exc_traceback = sys.exc_info()
                    self.gui_view_text('Import Entities failed',
                        traceback.format_exception(
                            exc_type, exc_value, exc_traceback),
                            width=640, height=480)
                    traceback.print_exc()
                else:
                    file_handle.close()
                    # Add the entities to the world.
                    entities = locals_dict['entities']
                    State.world.add(*entities)
                # Put the mouse shape back.
                State.world.add(self.mouse_shape)
        
    # MapEditor.action_entities_import
    
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
            self.changes_unsaved = False
        except:
            exc_type,exc_value,exc_traceback = sys.exc_info()
            self.gui_view_text('Save Entities failed',
                traceback.format_exception(exc_type, exc_value, exc_traceback),
                width=640, height=480)
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
            self.gui_browse_file("Save Entities As",
                data.path['map'], self.action_entities_save_as)
        elif sub_action == 'file_picked':
            d = widget
            if d.value is not None:
                State.file_entities = d.value
                self.action_entities_save()
    
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
        # Intercept RETURN and ESCAPE for convenient switch between map-editing
        # key control and user_data input.
        user_data = self.gui_form['user_data']
        if user_data.container.myfocus is user_data:
            if key in (K_ESCAPE,):
                user_data.blur()
                return
        elif key == K_RETURN and self.selected is not None:
            user_data.focus()
            return
        # Filter out keystrokes that are "ugly" in GUI.
        if key not in (K_DELETE,):
            self.gui.event(e)
        ## Customization: beware of key conflicts with pgu.gui.
        if not self.modal:
            if key in (K_DELETE,K_KP_PERIOD):
                if self.selected and not user_data.container.myfocus is user_data:
                    shape = self.selected 
                    self.deselect()
                    State.world.remove(shape)
            elif key == K_ESCAPE:
                self.action_quit_app()
            elif key == K_v and mod & KMOD_CTRL:
                self.verbose = not self.verbose
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
        elif self.modal:
            # Modal dialog hogs mouse clicks.
            self.gui.event(e)
            return
        
        # If click on widget, pass event to GUI. Else it is an editor action.
        widget = self.gui_hover()
        user_data = self.gui_form['user_data']
        if widget is not None:
            if widget is user_data:
                if self.selected is None:
                    return
            self.gui.event(e)
        else:
            if self.gui.widget.myfocus is self.gui_form['side_panel']:
                user_data.blur()
            self.mouse_down = button
            self.action_mouse_click(e)
    
    def on_mouse_motion(self, e, pos, rel, buttons):
        """Handler for MOUSEMOTION events.
        """
        self.mouse_shape.position = State.camera.screen_to_world(pos)
        State.world.add(self.mouse_shape)
        if self.mouse_down:
            self.action_mouse_drag(e)
        else:
            self.gui.event(e)
    
    def on_mouse_button_up(self, e, pos, button):
        """Handler for MOUSEBUTTONUP events.
        """
        self.gui.event(e)
        if self.mouse_down == button:
            # Crossing GUI widgets does not interfere with drag-and-release.
            self.action_mouse_release(e)
            self.mouse_down = 0
    
    def on_resize(self, e, screen_size, w, h):
        """Handler for VIDEORESIZE events.
        """
        # Update the pygame display mode and Gummworld2 camera view.
        if w < 800: w = 800
        if h < 600: h = 600
        screen_size = w,h
        State.screen = Screen(screen_size, RESIZABLE)
        State.camera.view = View(State.screen.surface, Rect(0,0,w*2/3,h))
        State.screen.eraser.fill(Color('grey'))
        
        # Resize the widgets.
        self.gui.screen = State.screen.surface
        self.gui.resize()
        self.remake_scrollbars(reset=False)
        c = self.gui.widget
        side_panel = self.gui_form['side_panel']
        c.remove(side_panel)
        make_side_panel(c)
    
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
#        return 'S'+str(s) + ' W'+str((int(w.x),int(w.y),))
        return 'S%s W%s@%s' % (str(s), str((int(w.x),int(w.y),)),
            State.world.level_of(State.app.mouse_shape))
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
        return 'None' if shape is None else '%s@%d/%d'%(
            shape.rect.center, State.world.level_of(shape), State.world.num_levels)
    State.hud.add('Selected',
        Statf(next_pos(), 'Selected %s', callback=get_selected, interval=100))
    
# make_hud


def make_menus(container):
    """Make GUI menus for content control.
    """
    app = State.app
    menus = gui.Menus([
        ('File/Quit',        app.action_quit_app, None),
        ('Entities/Import',  app.action_entities_import, None),
        ('Entities/Save',    app.action_entities_save, None),
        ('Entities/Save As', app.action_entities_save_as, None),
        ('Entities/Clear',   app.action_entities_clear, None),
        ('Images/New Map',   app.action_map_new, None),
        ('Images/Load Map',  app.action_map_load, None),
        ('Images/Load Tiles',app.action_tiles_load, None),
        ('View/Grid',        app.action_view_grid, None),
        ('View/Labels',      app.action_view_labels, None),
        ('View/Rects',       app.action_view_rects, None),
        ('View/HUD',         app.action_view_hud, None),
    ], name='menus')
    container.add(menus, 1, 1)
    menus.rect.w,menus.rect.h = menus.resize()
    
# make_menus


def make_toolbar(container):
    """Make GUI toolbar with shape tools in it.
    """
    app = State.app
    g = gui.Group(name='toolbar_group', value='rect_tool')
    h = app.gui_form['menus'].rect.height
    t = gui.Table(name='toolbar')
    t.tr()
    t.td(gui.Tool(g, gui.Label('Rect'), 'rect_tool', height=h))
    t.td(gui.Tool(g, gui.Label('Triangle'), 'triangle_tool', height=h))
    t.td(gui.Tool(g, gui.Label('Quad'), 'quad_tool', height=h))
    t.td(gui.Tool(g, gui.Label('Poly'), 'poly_tool', height=h))
    t.td(gui.Tool(g, gui.Label('Circle'), 'circle_tool', height=h))
    x = app.gui_form['menus'].rect.right + 2
    container.add(t, x, 0)
    return g,t
    
# make_toolbar


def make_side_panel(container):
    """GUI Table with shape info and other editing tools.
    """
    t = gui.Table(name='side_panel', align=1, valign=-1)
    
    # Shape type.
    t.tr()
    t.td(gui.Label('Type:'))
    t.td(gui.Label('no selection', name='shape_type'), align=-1)
    
    # Shape position.
    t.tr()
    t.td(gui.Label('Pos:'))
    t.td(gui.Label('', name='shape_pos'), align=-1)
    
    # Shape user_data.
    t.tr()
    label = gui.Label('Data:')
    t.td(label)
    smaller_font = pygame.font.Font(data.filepath('font', 'Vera.ttf'), 10)
    w = (State.screen.width - State.camera.view.width - label.resize()[0] - 20)
    user_data = gui.TextArea(
        value='', name='user_data', font=smaller_font, width=w)
    user_data.connect(gui.CHANGE, State.app.action_set_userdata, user_data)
    t.td(user_data)
#    # Add image to user_data button.
#    t.tr()
#    t.td(gui.Button('Add image to user_data'), colspan=2)
    
    # Image palette: table in a scroll area.
    t.tr()
    t.td(gui.Spacer(1,6), colspan=2)
    t.tr()
    t.td(gui.Label('Images:'), colspan=2, align=-1)
    t.tr()
    w = (State.screen.width - State.camera.view.width - 13)
    h = (State.screen.height - t.resize()[1] - 3)
    tile_palette = gui.Table(name='tile_palette')
    tile_scroller = gui.ScrollArea(tile_palette, width=w, height=h)
    t.td(tile_scroller, colspan=2, align=1)

    x,y = State.camera.view.width,0
    container.add(t, x, y)

# make_form_shape_info


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
