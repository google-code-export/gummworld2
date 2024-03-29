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


__doc__ = """world_editor.py - A world editor for Gummworld2.
"""

HELP_TEXT = """
Saving and loading is fully implemented. The file format may change over time as features are added. However, efforts will be made to keep tools backwards compatible. Finally, the file contents are simply URL-quoted ASCII which should be easy to convert.

Controls

    * Menus do what you'd expect.
    * Scrollbars do what you'd expect.
    * Toolbar selects a shape to insert into the map.

    * Right-click in the map:
        * Inserts a shape into the map. If tiles are attached to the mouse, they are attached to the shape when it is inserted.

    * Left-click in the map:
        * Clicking inside a shape selects that shape for further manipulation.
        * Clicking outside a shape deselects the selected shape.
        * Clicking inside stacked shapes selects the next shape.
        * Clicking a shape's control point selects the control point.
        * Clicking and dragging the center control point moves the shape.
        * Clicking and dragging a corner control point reshapes a shape.

    * Left-click in the tile palette:
        * Clicking on an unselected tile selects that tile. All other tiles are deselected.
        * Clicking on a selected tile deselects all tiles.

    * Right-click in the tile palette:
        * Adds or removes a tile from multiple selection.

    * Keys:
        * Delete: Delete a shape and its attached tiles from the map.
        * Enter,Escape: Enter and leave the user data input field for the selected shape.
        * Left,Right,Up,Down: Move an entire shape if the center control point is selected; else, move the selected vertex.
        * Minus,Equals: Scale a shape.
        * Ctrl-C, Ctrl-X, Ctrl-V: Cut-copy-paste the selected shape.
        * Tab: Cycle shape color scheme for visibility.

What are the double lines?

    These are guide lines for QuadTree which is included in the distribution. If the game will be using WorldQuadTree, it's recommended to keep static objects out of the quadtree's layer 1.

    Wherever a red double line crosses an orange one an object at that location will be pushed up to layer 1. Keeping objects in layer 1 is expensive. It increases the number of unnecessary collision checks each time a mobile object repositions. One can control the size and location of static objects, so it makes perfect sense to avoid, where possible, letting static objects overlap these junctions.

    The HUD also gives clues about QuadTree layers: The "Selected" item shows a shape's location and its level in the quadtree; and the "In Top Level" item indicates how many world entities are in level 1.
"""

"""
Design:
    There is a form in the space on the right. Selecting a shape will allow data
    entered into the form to be attached to the shape, and data already attached
    will be displayed in the form. World loader routines can then use that data
    for any robust purpose.
    
    Below the form in the space on the right is a tile palette. This is for
    decorating the map so that one can see the graphics for spawned and/or
    collidable objects while sizing their shapes for the world.
    
    Beyond the essentials, there is a fluid wish list of features which may get
    added as demand dictates and time permits.

Basic to do (complete for 1.0 release):
    [X] Geometry classes auto-size their points to fit selected tiles.
    [X] Form for picking images.
        [X] Loader/sizer.
        [X] Palette.
        [X] Picking from palette.
        [X] Stamp, move, delete in map.
        [X] Autosave/load tilesheet meta data so it doesn't have to be
            input every time a tilesheet is loaded. Meta data saved in the same
            directory as the source image file, named "basename.tilesheet". The
            format is one line, space-delimited ASCII:
                marginx marginy tilewidth tileheight spacingx spacingy
    [X] Selected tiles attached to mouse pointer for placement.
    [X] Selected tiles attached to world shapes.
    [X] Form for user_data.
        [X] Auto-add tilesheet/tile info to user_data (tilesheet name, tile
            rects).
    [X] Export/import shape and tile data.
    [X] action_map_new() with Size Form.
    [X] Single operations: Cut, copy, paste.
    [X] Contrast aid: Cycle through color schemes for world shapes.
    [X] Help viewer.
    [X] QuadTree 1.5 grid lines.
    [X] Menu toggle for QuadTree grid lines.
    [X] HUD item to alert about shapes in top level.
    [X] Dialog to remove tilesheets from the palette.

Advanced to do:
    [_] Tilesheets.
        [_] Add a list to side panel to show open tilesheet names.
        [_] Picking tilesheet name from list loads it in palette.
        [_] No more need to close tilesheets. Get rid of dialog.
        [_] When world importer loads tilesheets, open the tile sheet sizer
            dialog for each image file that does not have a tilesheet meta file.
            Do not load images if the dialog is canceled.
        [_] Tool: Strip tile info from user_data if no tilesheet is loaded.
        [_] Tool: Attach or replace tiles for a shape.
    [_] Undo, redo.
    [_] Put more thought into working with shapes. e.g. PITA to size a shape
        after every insert. Maybe: a list for history; a customizable imported
        list. Note: copy-paste and key-grab helps with this a lot.
    [_] Chooser: Importer and exporter (e.g., ASCII, pickle, custom).
    [_] Productivity:
        [_] Shape templates: Make a shape, add to template list. Choose from
            list to insert "cookie cut" shapes.
        [_] User_data templates: a la Shape templates.
        [_] Group operations: Delete, move; cut, copy, paste?
    [_] Proof-reading:
        [_] List unique user_data and count. Click list item to go to shapes.
    [_] Clicking on map while dragging scrollbar inserts a shape. Probably
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
from gummworld2 import (
    model, data, geometry, toolkit, pygame_utils,
    State, Camera, Map, Screen, View,
    HUD, Stat, Statf,
    GameClock, Vec2d,
)
import gui


# These lambdas place points at calculated positions given a bounding rect. This
# dict is a lookup for tool types. See make_toolbar(), action_mouse_click(), and
# the *Geom classes.
POLY_POINT_SETS = dict(
    triangle_tool=lambda r: [
        Vec2d(r.centerx,0),
        Vec2d(r.bottomright),
        Vec2d(r.bottomleft),
    ],
    quad_tool=lambda r: [
        Vec2d(r.topleft),
        Vec2d(r.topright),
        Vec2d(r.bottomright),
        Vec2d(r.bottomleft),
    ],
    pent_tool=lambda r: [
        Vec2d(r.centerx,0),
        Vec2d(r.w,round(r.h*2.0/5)),
        Vec2d(round(r.w*4.0/5),r.h),
        Vec2d(round(r.w*1.0/5),r.h),
        Vec2d(0,round(r.h*2.0/5)),
    ],
)

# When the key is pressed, move the selected shape by this amount.
KEY_SHAPE_STEP = {
    K_LEFT : -1,
    K_RIGHT : 1,
    K_UP : -1,
    K_DOWN : 1,
}

class GeomColors(object):
    which = 0
    values = [
        ## n=normal, h=hover, c=copy, x=cut
        dict(n=Color(190,190,190,150),h=Color(255,255,255,150),c=Color(255,165,0,150),x=Color(255,0,0,150)),
        dict(n=Color(160,160,160,150),h=Color(225,225,225,150),c=Color(225,135,0,150),x=Color(225,0,0,150)),
        dict(n=Color(130,130,130,150),h=Color(195,195,195,150),c=Color(195,105,0,150),x=Color(195,0,0,150)),
    ]
    
    def get(self, obj):
        app = State.app
        sel = app.selected
        hover = app.mouseover_shapes
        paste = app.paste
        v = self.values[self.which]
        if paste is not None and obj in paste:
            if 'cut' in paste: return v['x']
            if 'copy' in paste: return v['c']
        if obj in hover: return v['h']
        return v['n']
    
    def next(self):
        self.which += 1
        if self.which == len(self.values):
            self.which = 0

GEOM_COLORS = GeomColors()


# I hate this kludge...
os.environ['SDL_VIDEO_WINDOW_POS'] = '7,30'
#os.environ['SDL_VIDEO_CENTERED'] = '1'


class Tile(gui.Image):
    """This is an Image that represents a spritesheet tile. It exists in a
    gui.Document within a gui.Scrollarea. ENTER and EXIT events trigger
    mouseover highlighting. CLICK events trigger State.app.selected_tiles add
    and removal.
    """
    
    tile_hovering = None
    tile_selected = None
    
    def __init__(self, value, file_path, rect, tilesheet, tile_id, **params):
        gui.Image.__init__(self, value.copy(), **params)
        self.tile_file_path = file_path
        self.tile_rect = rect
        self.tile_tilesheet = tilesheet
        self.tile_id = tile_id
        # Copy of source image.
        self.tile_image = pygame.surface.Surface(rect.size)
        self.tile_image.blit(self.value, (0,0))
        if self.tile_hovering is None:
            # An alpha image used as a hover mask.
            self.tile_hovering = pygame.surface.Surface(rect.size)
            self.tile_hovering.fill(Color(140,200,250))
            pygame.draw.rect(self.tile_hovering, Color('blue'), self.tile_hovering.get_rect(), 1)
            self.tile_hovering.set_alpha(99)
            # An alpha image used as a selected mask.
            self.tile_selected = pygame.surface.Surface(rect.size)
            self.tile_selected.fill(Color(140,250,250))
            pygame.draw.rect(self.tile_selected, Color('blue'), self.tile_selected.get_rect(), 1)
            self.tile_selected.set_alpha(99)
        # Translucent mouse image.
        self.mouse_image = self.tile_image.copy()
        self.mouse_image.set_alpha(75)
        # State indicators.
        self.tile_is_selected = False
        self.tile_is_hovering = False
    
    def tile_deselect(self):
        self.value.blit(self.tile_image, (0,0))
        self.tile_is_selected = False
        try:
            State.app.selected_tiles.remove(self)
        except:
            pass
    
    def tile_select(self):
        self.value.blit(self.tile_image, (0,0))
        self.value.blit(self.tile_selected, (0,0))
        self.tile_is_selected = True
        self.tile_is_hovering = False
        State.app.selected_tiles.append(self)
    
    def event(self, e):
        if e.type == gui.CLICK:
            if e.button == 1:
                selected = State.app.selected_tiles
                self_selected = self.tile_is_selected
                for tile in selected[:]:
                    tile.tile_deselect()
                if not self_selected:
                    self.tile_select()
            elif e.button == 3:
                selected = State.app.selected_tiles
                if self in selected:
                    self.tile_deselect()
                else:
                    self.tile_select()
        elif e.type == gui.ENTER:
            if not self.tile_is_selected:
                self.value.blit(self.tile_image, (0,0))
                self.value.blit(self.tile_hovering, (0,0))
                self.tile_is_hovering = True
        elif e.type == gui.EXIT:
            if not self.tile_is_selected:
                self.value.blit(self.tile_image, (0,0))
                self.tile_is_hovering = False
#        else:
#            print e.type, self.tile_rect


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
    image_grabbed = None
    
    def __init__(self, parent, attr):
        super(ControlPoint, self).__init__(0,0,7,7)
        if self.image is None:
            self.image = pygame.surface.Surface((7,7))
            self.image.fill(Color('yellow'))
            self.image_grabbed = pygame.surface.Surface((7,7))
            self.image_grabbed.fill(Color('red'))
        self.parent = parent
        self.attr = attr
        self._position = Vec2d(self.center)
        
    # ControlPoint.__init__
    
    def set_position(self, val):
        x,y = val
        p = self._position
        p.x,p.y = x,y
        self.center = round(x),round(y)
    
    @property
    def position(self):
        return self._position
    @position.setter
    def position(self, val):
        self.set_position(val)
        self.parent.adjust(self, self.attr)
        
    # ControlPoint.position

class RectGeom(geometry.RectGeometry):
    """RectGeom(x, y, w, h, pos) : RectGeom
    RectGeom(tiles, pos) : RectGeom
    """
    
    typ = 'Rect'
    draw_rect = pygame.draw.rect
    
    def __init__(self, *args):
        if len(args) > 2:
            tiles = []
            super(RectGeom, self).__init__(*args)
        else:
            tiles,pos = args
            x,y,w,h = tiles_bounding_rect(tiles)
            super(RectGeom, self).__init__(x, y, w, h, pos)
        self._attrs = 'topleft','topright','bottomright','bottomleft','center'
        self._cp = [ControlPoint(self, self._attrs[i]) for i in range(5)]
        self.grabbed = None
        self.user_data = ''
        self.tiles = tiles[:]
        # Add tile info to user_data
        for tile in tiles:
            name = data.relpath(tile.tile_file_path)
            idx = str(tile.tile_id)
            self.user_data += ' '.join(['tile', idx, name]) + '\n'
        
    # RectGeom.__init__
    
    @property
    def control_points(self):
        controls = self._cp
        r = self.rect
        attrs = self._attrs
        for i,cp in enumerate(controls):
            cp.set_position(getattr(r, attrs[i]))
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
    
    def inflate(self, x, y):
        self.rect.inflate_ip(x, y)
        self.control_points
        
    # RectGeom.inflate
    
    def copy(self):
        if len(self.tiles):
            dupe = RectGeom(self.tiles, self.position)
        else:
            dupe = RectGeom(*tuple(self.rect))
        return dupe
    
    # RectGeom.copy
    
    def draw(self):
        app = State.app
        camera = State.camera
        surface = camera.surface
        world_to_screen = camera.world_to_screen
        # Tile image.
        draw_tiles(self.position, self.tiles)
        # Indicate mouse-over, copy, or cut.
        color = GEOM_COLORS.get(self)
        # Draw rect in screen space.
        r = self.rect.copy()
        r.center = world_to_screen(self.rect.center)
        self.draw_rect(surface, color, r, 1)
        # If shape is selected, draw control points in screen space.
        if self is app.selected:
            for cp in self.control_points:
                if cp is self.grabbed:
                    surface.blit(cp.image_grabbed, world_to_screen(cp.topleft))
                else:
                    surface.blit(cp.image, world_to_screen(cp.topleft))
        
    # RectGeom.draw


class PolyGeom(geometry.PolyGeometry):
    
    typ = 'Poly'
    draw_poly = pygame.draw.polygon
    draw_rect = pygame.draw.rect
    
    def __init__(self, points, pos, tiles=[], auto=False):
        
        if auto:
            if len(tiles):
                rect = tiles_bounding_rect(tiles)
                rect.topleft = 0,0
                points = points(rect)
            else:
                rect = Rect(0,0,64,64)
                points = points(rect)
        super(PolyGeom, self).__init__(points, pos)
        
        self.tmp_rect = self.rect.copy()
        self._cp = [ControlPoint(self, i) for i in range(len(self._points)+1)]
        self._cp = self.control_points
        self.grabbed = None
        self.user_data = ''
        self.tiles = tiles[:]
        self._angles = [-1] * len(self._points)
        self._ratios = [None] * len(self._points)
        # Add tile info to user_data
        for tile in tiles:
            name = data.relpath(tile.tile_file_path)
            idx = str(tile.tile_id)
            self.user_data += ' '.join(['tile', idx, name]) + '\n'
        
    # PolyGeom.__init__
    
    @property
    def control_points(self):
        controls = self._cp
        points = self.points
        for i,p in enumerate(points):
            controls[i].set_position(p)
        i += 1
        controls[i].set_position(self.rect.center)
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
            self.position = cp.position
        else:
            # Poly point grabbed. Recalculate rect in world space.
            controls = controls[:-1]
            xvals = [c.position.x for c in controls]
            yvals = [c.position.y for c in controls]
            xmin = reduce(min, xvals)
            width = reduce(max, xvals) - xmin + 1
            ymin = reduce(min, yvals)
            height = reduce(max, yvals) - ymin + 1
            self.rect.topleft = round(xmin),round(ymin)
            self.rect.size = round(width),round(height)
            p = self._position
            p.x,p.y = xmin+width/2, ymin+height/2
            
            # Recalculate points in local space relative to rect.
            topleft = Vec2d(xmin,ymin)
            points = self._points
            for i,c in enumerate(controls):
                self._angles[i] = -1
                self._ratios[i] = None
                points[i] = c.position - topleft
        
    # PolyGeom.adjust
    
    def inflate(self, x, y):
        """Generally you want to inflate by a factor of 2 or the rect's center
        will shift.
        """
        rect = self.rect.inflate(x, y)
        if rect.w <= 0 or rect.h <= 0:
            return
        
        rect = self.rect.copy()
        rect.topleft = 0,0
        self.rect.inflate_ip(x, y)
        
        for i,p in enumerate(self._points):
            if self._ratios[i] is None:
                xrat = float(p.x) / (rect.w-1)
                yrat = float(p.y) / (rect.h-1)
                ratio = Vec2d(xrat,yrat)
                self._ratios[i] = ratio
            else:
                ratio = self._ratios[i]
            xnew = (self.rect.w-1) * ratio.x
            ynew = (self.rect.h-1) * ratio.y
            p.x,p.y = xnew,ynew
        self.control_points
        
    # PolyGeom.inflate
    
    def copy(self):
        dupe = PolyGeom(
            [(p.x,p.y) for p in self._points],
            self.position,
            tiles=self.tiles)
        return dupe
    
    # PolyGeom.copy
    
    def draw(self):
        app = State.app
        camera = State.camera
        surface = camera.surface
        world_to_screen = camera.world_to_screen
        # Tile image.
        draw_tiles(self.position, self.tiles)
        # Indicate mouse-over, copy, or cut.
        color = GEOM_COLORS.get(self)
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
                if cp is self.grabbed:
                    surface.blit(cp.image_grabbed, world_to_screen(cp.topleft))
                else:
                    surface.blit(cp.image, world_to_screen(cp.topleft))
        
    # PolyGeom.draw
    
    def _minvec(self, seq, i):
        """Return the minimum elements in seq. i is the index to compare: 0 is
        x, 1 is y.
        """
        minv = []
        for v in seq:
            if len(minv):
                v1 = minv[0]
                if v[i] < v1[i]:
                    minv[:] = [v]
                elif v[i] == v1[i]:
                    minv.append(v)
            else:
                minv.append(v)
        return minv
        
    # PolyGeom._minvec
    
    def _maxvec(self, seq, i):
        """Return the maximum elements in seq. i is the index to compare: 0 is
        x, 1 is y.
        """
        maxv = []
        for v in seq:
            if len(maxv):
                v1 = maxv[0]
                if v[i] > v1[i]:
                    maxv[:] = [v]
                elif v[i] == v1[i]:
                    maxv.append(v)
            else:
                maxv.append(v)
        return maxv
        
    # PolyGeom._maxvec

class CircleGeom(geometry.CircleGeometry):
    """CircleGeom(origin, radius) : CircleGeom
    CircleGeom(origin, tiles) : CircleGeom
    """
    
    typ = 'Circle'
    draw_circle = pygame.draw.circle
    draw_rect = pygame.draw.rect
    
    def __init__(self, origin, radius_or_tiles):
        if isinstance(radius_or_tiles, (int,float)):
            tiles = []
            radius = radius_or_tiles
        else:
            tiles = radius_or_tiles
            rect = tiles_bounding_rect(tiles)
            radius = max(rect.w,rect.h) // 2
        super(CircleGeom, self).__init__(origin, radius)
        
        self._attrs = 'radius','origin'
        self._cp = [ControlPoint(self, self._attrs[i]) for i in range(2)]
        self.grabbed = None
        self.user_data = ''
        self.tiles = tiles[:]
        # Add tile info to user_data
        for tile in tiles:
            name = data.relpath(tile.tile_file_path)
            idx = str(tile.tile_id)
            self.user_data += ' '.join(['tile', idx, name]) + '\n'
        
    # CircleGeom.__init__
    
    @property
    def control_points(self):
        controls = self._cp
        r = self.rect
        controls[0].set_position(geometry.point_on_circumference(
            self.origin, self.radius, 180.0))
        controls[1].set_position(self.rect.center)
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
    
    def inflate(self, x, y):
        self.radius += x // 2
        self.control_points
        
    # CircleGeom.inflate
    
    def copy(self):
        if len(self.tiles):
            shape = CircleGeom(self.origin, self.tiles)
        else:
            shape = CircleGeom(self.origin, self.radius)
        return shape
    
    # CircleGeom.copy
    
    def draw(self):
        app = State.app
        camera = State.camera
        surface = camera.surface
        world_to_screen = camera.world_to_screen
        # Tile image.
        draw_tiles(self.position, self.tiles)
        # Indicate mouse-over, copy, or cut.
        color = GEOM_COLORS.get(self)
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
                if cp is self.grabbed:
                    surface.blit(cp.image_grabbed, world_to_screen(cp.topleft))
                else:
                    surface.blit(cp.image, world_to_screen(cp.topleft))
        
    # CircleGeom.draw


class MapEditor(object):
    """The Beast.
    """
    
    def __init__(self):
        
        State.app = self
        
        tile_size = 128,128
        map_size = 10,10
        
        screen_size = Vec2d(1024,768)
        screen_size = Vec2d(800,600)
        
        # Set up the Gummworld2 state.
        State.clock = GameClock(30, 30)
        State.screen = Screen(screen_size, RESIZABLE)
        State.map = Map(tile_size, map_size)
        State.camera = Camera(
            model.QuadTreeObject(Rect(0,0,5,5)),
            View(State.screen.surface, Rect(0,0,screen_size.x*2/3,screen_size.y))
        )
        self.world_grids = []
        self.make_world()
        pygame.display.set_caption('Gummworld2 World Editor')
        x,y = State.camera.view.rect.topleft
        w,h = Vec2d(screen_size) - (State.camera.view.rect.right,0)
        State.gui_panel = View(State.screen.surface, Rect(x,y,w,h))
        State.screen.eraser.fill(Color('grey'))
        
        # Mouse details.
        #   mouse_shape: world entity for mouse interaction.
        #   mouse_down: mouse button currently held down.
        #   selected: world entity currently selected.
        #   selected_tiles: selections in tile palette.
        #   mouseover_shapes: list of shapes over which the mouse is hovering.
        self.mouse_shape = RectGeom(0,0,5,5)
        self.mouse_down = 0
        self.selected = None
        self.selected_tiles = []
        self.grabbed_by_mouse = False
        self.mouseover_shapes = []
        
        # Keyboard details.
        pygame.key.set_repeat(150, 1000/30)
        self.paste = None
        
        # Some things to aid debugging.
        self.time = TimeThing('%M%S')
        self.verbose = False
        
        # Gooey stuff.
        self.gui = None
        self.gui_form = None
        self.tilesheets = []
        self.modal = None
        self.changes_unsaved = False
        self.make_gui()
        # Scrollbar position sets camera pos. The following sets it absolutely,
        # without waiting for events or interpolation. It's a cosmetic thing.
        State.camera.init_position(State.camera.position)
        
        # Files.
        State.file_entities = None
        State.file_map = None
        
        # Make some default content and HUD.
        toolkit.make_tiles2()
        make_hud()
        State.show_hud = True
        State.show_grid = True
        State.show_labels = True
        State.show_rects = False
        State.show_world_grid = True
        
        ## Test code to launch tilesheet sizer at startup.
        if False:
            self.gui_tilesheet_sizer(
                data.filepath('image','test.png'), self.action_tiles_load)
        
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
            State.hud.update(State.clock.update_elapsed)
    
    def update_gui(self):
        """Update the GUI, then update the app from the GUI.
        """
        # Plucked from gui.App.loop().
        self.gui.set_global_app()
        self.gui.update()
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
        State.screen.clear()
        toolkit.draw_tiles()
        toolkit.draw_labels()
        toolkit.draw_grid()
        self.draw_world()
        if State.show_hud:
            State.hud.draw()
        self.draw_mouse()
        self.gui.paint()
        State.screen.flip()
    
    def draw_world(self):
        """Draw the on-screen shapes in the world.
        """
        mouse_shape = self.mouse_shape
        selected = self.selected
        things = State.world.entities_in(State.camera.rect)
        camera = State.camera
        blit = camera.view.surface.blit
        world_to_screen = camera.world_to_screen
        if State.show_world_grid:
            for grid_line in self.world_grids:
                blit(grid_line.image, world_to_screen(grid_line.rect.topleft))
        for thing in things:
            if thing not in (mouse_shape,selected):
                thing.draw()
        if selected:
            selected.draw()
    
    def draw_mouse(self):
        """Draw tiles that are attached to the mouse.
        """
        selected = self.selected_tiles
        if len(selected):
            if not self.gui_hover():
                draw_tiles(self.mouse_shape.position, selected, alpha=75)
    
    def select(self, shape):
        """Select a shape and update the form with its info.
        """
        if shape is None:
            return
        self.selected = shape
        selected = shape
        selected.grabbed = selected.control_points[-1]
        x,y = selected.position
        gui_form = self.gui_form
        gui_form['shape_type'].set_text(selected.typ)
        gui_form['shape_pos'].set_text(str((int(round(x)),int(round(y)))))
        gui_form['user_data'].value = selected.user_data
    
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
    
    def set_stamp(self, tilesheet, rect, surf):
        """Set tiles and info attached to the mouse for insertion in the map.
        """
        self.stamp = [surf, rect, tilesheet]
    
    def set_entities_file(self, val):
        """Set the entities file name in State, and update the HUD.
        """
        State.file_entities = val
        if val is None:
            val = 'none'
        else:
            val = data.relpath(val)
        State.hud.stats['Save File'].set_value(val)
    
    def make_world(self):
        """Create the world and populate its entities. Make grid lines as
        visual aid for quadtree.
        """
        if State.world is not None:
            entities = State.world.entity_branch.keys()
        else:
            entities = []
        State.world = model.WorldQuadTree(
            State.map.rect, worst_case=99, collide_entities=True)
        State.world.add(*entities)
        State.camera.position = State.camera.view.center
        del self.world_grids[:]
        num_levels = State.world.num_levels
        top_rect = State.world.rect
        worst_case = -State.world.worst_case if State.world.worst_case else 0
        def make_grid(branch):
            level = branch.level
            do_me = level == 2      # this displays critical top-level grids
            if do_me:
                rect = branch.rect
                alpha = 305 - float(level-1)/(num_levels-1)*255
                if level == 2:
                    if branch.branch_id > 4:
                        color = Color('red')
                        alpha = 255
                    else:
                        color = Color('orange')
                elif level == 3:
                    color = Color('yellow')
                elif level == 4:
                    color = Color('green')
                if rect.x in (0,worst_case):
                    # Horizontal line.
                    s = pygame.sprite.Sprite()
                    s.image = pygame.surface.Surface((top_rect.w,3))
                    s.rect = s.image.get_rect()
                    s.rect.centery = rect.bottom
                    s.image.fill(color)
                    pygame.draw.line(s.image, Color('black'), (0,1),(s.rect.w,1))
                    s.image.set_colorkey(Color('black'))
                    s.image.set_alpha(alpha)
                    self.world_grids.append(s)
                if rect.y in (0,worst_case):
                    # Vertical line.
                    s = pygame.sprite.Sprite()
                    s.image = pygame.surface.Surface((3,top_rect.h))
                    s.rect = s.image.get_rect()
                    s.rect.centerx = rect.right
                    s.image.fill(color)
                    pygame.draw.line(s.image, Color('black'), (1,0),(1,s.rect.h))
                    s.image.set_colorkey(Color('black'))
                    s.image.set_alpha(alpha)
                    self.world_grids.append(s)
            for b in branch.branches:
                make_grid(b)
        make_grid(State.world)
    
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
        if State.app.modal is not None:
            State.app.modal.close()
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
        self.gui_modal_off()
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
    
    def gui_tilesheet_sizer(self, file_path, callback):
        """Dialog to size a tilesheet.
        """
        d = self.modal
        def mk_inputs(*args):
            # Return a grouping of Inputs.
            c = gui.Document()
            for name,value in args:
                w = gui.Input(value=value, name=name, size=3)
                c.add(w)
            return c
        def draw_grid(form):
            # Overlay the tile sheet image with a grid to show results of dialog
            # input values.
            def get(name, minval=0):
                # Convert widget's string value to int.
                try:
                    val = int(form[name].value)
                    return max(val, minval)
                except ValueError:
                    return minval
            # Get the Input widgets' values.
            mx,my = get('tile_mx',0),get('tile_my',0)
            tx,ty = get('tile_tx',1),get('tile_ty',1)
            sx,sy = get('tile_sx',0),get('tile_sy',0)
            # Get the Image widget.
            image = form['tilesheet']
            # Attach to dialog "d" a rects list that can be used to carve up the
            # tiles, and a values list that holds the form input values used to
            # produce the rects.
            del d.rects[:]
            d.values[:] = mx,my,tx,ty,sx,sy
            # Copy the image so we can mark it up for GUI display.
            surf = image.value = image._value_orig.copy()
            surf_rect = surf.get_rect()
            # Make an alpha mask the size of a single tile.
            mask = pygame.surface.Surface((tx,ty))
            mask.fill(Color('blue'))
            pygame.draw.rect(mask, Color('cornflowerblue'), mask.get_rect(), 1)
            mask.set_alpha(99)
            # Carve up the tile sheet, working in margin and spacing offsets.
            # Blit the alpha mask over each tile as a visual aid in choosing
            # the form values.
            w,h = surf_rect.size
            nx,ny = w//tx, h//ty
            for y in range(ny):
                for x in range(nx):
                    rx = mx + x * (tx + sx)
                    ry = my + y * (ty + sy)
                    rect = Rect(rx,ry,tx,ty)
                    surf.blit(mask, rect)
                    d.rects.append(rect)
        # Check for and load tilesheet definition.
        defaults = toolkit.get_tilesheet_info(file_path)
        # Tile sheet dimensions.
        t = gui.Table()
        t.tr()
        t.td(gui.Label('Margin (w,h):'))
        t.td(mk_inputs(('tile_mx',defaults[0]), ('tile_my',defaults[1])), align=-1)
        t.tr()
        t.td(gui.Label('Tile (w,h):'))
        t.td(mk_inputs(('tile_tx',defaults[2]), ('tile_ty',defaults[3])), align=-1)
        t.tr()
        t.td(gui.Label('Spacing (w,h):'))
        t.td(mk_inputs(('tile_sx',defaults[4]), ('tile_sy',defaults[5])), align=-1)
        
        # Sizer gadgets.
        t.tr()
        image = gui.Image(file_path, name='tilesheet')
        image._value_orig = image.value.copy()
        s = gui.ScrollArea(image, 320, 200)
        t.td(s, colspan=2)
        
        # Ok, Cancel buttons.
        t.tr()
        c = gui.Document()
        c.add(gui.Button(gui.Label('Ok'), name='dialog_ok'))
        c.add(gui.Button(gui.Label('Cancel'), name='dialog_cancel'))
        t.td(c, colspan=2)
        
        # Set the dialog and its widget connections...
        d = gui.Dialog(gui.Label('Tile Sheet Sizer'), t)
        ## Values that the caller will need.
        d.file_path = file_path
        d.image = image.value.copy()
        d.values = []
        d.rects = []
        # Connections.
        d.connect(gui.CLOSE, self.gui_modal_off, None)
        form = self.gui_form
        for suffix in ('mx','my','tx','ty','sx','sy'):
            form['tile_'+suffix].connect(gui.CHANGE, draw_grid, form)
        draw_grid(form)
        form['dialog_ok'].connect(gui.CLICK, callback, 'tilesheet_sized', d)
        form['dialog_ok'].connect(gui.CLICK, d.close, None)
        form['dialog_cancel'].connect(gui.CLICK, d.close, None)
        d.open()
        self.modal = d
    
    # MapEditor.gui_tilesheet_sizer
    
    def gui_tilesheet_closer(self):
        if not len(self.tilesheets):
            print 'gui_tilesheet_closer: no tilesheets'
            return
        def close_tilesheet(*args):
            tilesheet_list = self.gui_form['tilesheet_list']
            if tilesheet_list.value is not None:
                # Remove the item from self.tilesheets and the GUI list.
                i = tilesheet_list.value
                tilesheet_list.value = None
                tilesheet = self.tilesheets[i]
                del self.tilesheets[i]
                tilesheet_list.remove(i)
                # Renumber the GUI item values so they correspond with
                # self.tilesheets.
                i = 0
                for item in tilesheet_list.items:
                    item.value = i
                    i += 1
                # Remake the side panel.
                c = self.gui.widget
                side_panel = self.gui_form['side_panel']
                c.remove(side_panel)
                make_side_panel(c)
        # Dialog with a table.
        t = gui.Table()
        d = gui.Dialog(gui.Label('Close Tile Sheets'), t)
        # List for tilesheet filenames.
        tilesheet_list = gui.List(width=400, height=300, name='tilesheet_list')
        t.tr()
        t.td(tilesheet_list, colspan=2)
        # Build the list. Truncate program dir from filename so it fits.
        program_dir = pygame_utils.get_main_dir()
        i = 0
        for ts in self.tilesheets:
            file_path = os.path.relpath(ts.file_path, data.data_dir)
            tilesheet_list.add(file_path, value=i)
            i += 1
        # A couple buttons.
        t.tr()
        t.td(gui.Button(gui.Label('Close Tileset'), name='dialog_x'))
        t.td(gui.Button(gui.Label('Done'), name='dialog_done'))
        # Connections.
        d.connect(gui.CLOSE, self.gui_modal_off, None)
        form = self.gui_form
        form['dialog_x'].connect(gui.CLICK, close_tilesheet, None)
        form['dialog_done'].connect(gui.CLICK, d.close, None)
        d.open()
        self.modal = d
    
    # MapEditor.gui_tiles_heet_closer
    
    def gui_map_sizer(self, title, callback):
        """Dialog to size a new map.
        """
        d = self.modal
        
        def mk_inputs(*args):
            # Return a grouping of Inputs.
            c = gui.Document()
            for name,value in args:
                w = gui.Input(value=value, name=name, size=5)
                c.add(w)
            return c
        
        def update_values(form):
            def get(name):
                # Convert widget's string value to int.
                try:
                    return int(form[name].value)
                except ValueError:
                    return 0
            # Get the Input widgets' values.
            tx,ty = get('tile_sx'),get('tile_sy')
            mx,my = get('tile_sx'),get('tile_sy')
            d.values[:] = mx,my,tx,ty
        
        # Dialog and content.
        t = gui.Table()
        d = gui.Dialog(gui.Label(title), t)
        
        # Tile size inputs.
        t.tr()
        t.td(gui.Label('Tile size (w,h):'))
        t.td(mk_inputs(('tile_sx', ''), ('tile_sy', '')))
        
        # Map size inputs.
        t.tr()
        t.td(gui.Label('Map size (w,h):'))
        t.td(mk_inputs(('map_sx', ''), ('map_sy', '')))
        
        t.tr()
        t.td(gui.Spacer(1, 3))
        
        # Ok, Cancel buttons.
        t.tr()
        c = gui.Document()
        c.add(gui.Button(gui.Label('Ok'), name='dialog_ok'))
        c.add(gui.Button(gui.Label('Cancel'), name='dialog_cancel'))
        t.td(c, colspan=2)
        
        ## Values the caller will need.
        d.values = []
        # Connections.
        d.connect(gui.CLOSE, self.gui_modal_off, None)
        form = self.gui_form
        for name in ('map_sx','map_sy','tile_sx','tile_sy'):
            form[name].connect(gui.CHANGE, update_values, form)
        update_values(form)
        form['dialog_ok'].connect(gui.CLICK, callback, 'map_sized', d)
        form['dialog_ok'].connect(gui.CLICK, d.close, None)
        form['dialog_cancel'].connect(gui.CLICK, d.close, None)
        
        d.open()
        self.modal = d
    
    def action_set_userdata(self, user_data):
        """GUI input field changed, set the selected shape's user_data.
        """
        if self.selected is not None:
            self.selected.user_data = user_data.value
            self.changes_unsaved = True
    
    def action_shape_delete(self):
        """Delete shape action: delete the selected shape.
        """
        user_data = self.gui_form['user_data']
        if self.selected and not user_data.container.myfocus is user_data:
            shape = self.selected 
            self.deselect()
            State.world.remove(shape)
    
    def action_shape_copy(self):
        """Copy shape action: target the selected shape for copy-paste action.
        """
        if self.selected is None:
            self.paste = None
        else:
            self.paste = ('copy', self.selected)
    
    def action_shape_cut(self):
        """Cut shape action: target the selected shape for cut-paste action.
        """
        if self.selected is None:
            self.paste = None
        else:
            self.paste = ('cut', self.selected)
    
    def action_shape_paste(self):
        """Paste shape action: paste the cut or copied shape at the mouse
        location.
        """
        if self.paste is not None:
            action,shape = self.paste
            if action == 'cut':
                shape.position = self.mouse_shape.position
                State.world.add(shape)
                self.select(shape)
            elif action == 'copy':
                # new_shape = shape.copy()
                if isinstance(shape, (RectGeom,CircleGeom,PolyGeom)):
                    shape = shape.copy()
                    shape.position = self.mouse_shape.position
                    State.world.add(shape)
                    self.select(shape)
    
    # MapEditor.action_shape_paste
    
    def action_mouse_click(self, e):
        """Mouse click action: button 3 inserts a shape; button 1 selects,
        deselects or sizes a shape.
        """
        mouse_shape = self.mouse_shape
        mouseover_shapes = self.mouseover_shapes
        if not mouse_shape.rect.colliderect(State.camera.rect):
            # Don't change the map if clicking outside the map area.
            return
        elif self.modal is not None:
            # Don't change the map if a modal dialog is open.
            return
        elif self.mouse_down == 3:
            # Right-click: Put a shape.
            if self.selected not in mouseover_shapes:
                self.deselect()
            pos = State.camera.screen_to_world(e.pos)
            shape = self.gui_form['toolbar_group'].value
            tiles = self.selected_tiles
            if shape == 'rect_tool':
                if len(tiles):
                    geom = RectGeom(tiles, pos)
                else:
                    geom = RectGeom(0,0,64,64, pos)
            elif shape in POLY_POINT_SETS:
                points = POLY_POINT_SETS[shape]
                geom = PolyGeom(points, pos, tiles, auto=True)
            elif shape == 'circle_tool':
                if len(tiles):
                    geom = CircleGeom(pos, tiles)
                else:
                    geom = CircleGeom(pos, 32)
            else:
                return
            self.select(geom)
            State.world.add(geom)
            self.changes_unsaved = True
        elif self.mouse_down == 1:
            # Left-click: Select, deselect, or grab.
            if self.selected not in mouseover_shapes:
                self.deselect()
                if len(mouseover_shapes):
                    self.select(mouseover_shapes[0])
            elif self.selected is not None:
                if self.selected.grab(mouse_shape):
                    # Grabbed control point.
                    self.grabbed_by_mouse = True
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
                if grabbed is not None and self.grabbed_by_mouse:
                    grabbed.position = State.camera.screen_to_world(e.pos)
                    State.world.add(selected)
                    self.changes_unsaved = True
            x,y = selected.position
            self.gui_form['shape_pos'].set_text(str((int(round(x)),int(round(y)))))
        
    # MapEditor.action_mouse_drag

    def action_mouse_release(self, e):
        """Mouse release action: reset mouse-up state.
        """
        self.grabbed_by_mouse = False
    
    def action_key_grab_shape(self, key, mod):
        """Grab shape action: drag a grabbed control point using the keyboard.
        """
        selected = self.selected
        if selected and selected.grabbed is not None:
            grabbed = selected.grabbed
            speed = 4 if mod & KMOD_SHIFT else 1
            pressed = pygame.key.get_pressed()
            dirx,diry = 0,0
            if pressed[K_LEFT]: dirx += -1
            if pressed[K_RIGHT]: dirx += 1
            if pressed[K_UP]: diry += -1
            if pressed[K_DOWN]: diry += 1
            grabbed.position += (dirx*speed,diry*speed)
            State.world.add(self.selected)
            x,y = selected.position
            self.gui_form['shape_pos'].set_text(str((int(round(x)),int(round(y)))))
    
    def action_key_inflate_shape(self, key, mod):
        """Inflate shape action: de/inflate a shape.
        """
        selected = self.selected
        if selected:
            speed = 4 if mod & KMOD_SHIFT else 1
            pressed = pygame.key.get_pressed()
            x,y = 0,0
            if pressed[K_EQUALS]: x = y = 2
            if pressed[K_MINUS]: x = y = -2
            selected.inflate(x, y)
            State.world.add(self.selected)
    
    def action_map_new(self, sub_action=None, widget=None):
        """New map action: create a new map with default content.
        
        This is a reentrant method. The sub_action argument drives the behavior.
        It is called initially by an event handler, and again by GUI callback.
        """
        # Get map dimensions.
        if sub_action is None:
            self.gui_map_sizer('New Map Size', self.action_map_new)
        elif sub_action is 'map_sized':
            d = widget
            for v in d.values:
                if v <= 0:
                    self.gui_alert('Negative and zero values not allowed')
                    return
            map_size = d.values[0:2]
            tile_size = d.values[2:4]
            State.map = Map(tile_size, map_size)
            self.make_world()
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
                data.paths['map'], self.action_map_load)
        elif sub_action == 'file_picked':
            d = widget
            if d.value is not None:
                State.file_map = d.value
                # Import map.
                if State.file_map.endswith('.tmx'):
                    try:
                        State.map = toolkit.load_tiled_tmx_map(State.file_map)
                        self.make_world()
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
        """Load tile-sheet action: load a tile sheet from a supported image file
        and add the images to the tile palette.
        
        Also: import BASENAME.tilesheet, if found, to initialize the defaults in
        the tile sizer; save the tile sizer inputs to BASENAME.tilesheet.
        
        This is a reentrant method. The sub_action argument drives the behavior.
        It is called initially by an event handler, and again by GUI callback.
        """
        if sub_action is None:
            # Get input file name.
            self.gui_browse_file('Import Tiles',
                data.paths['image'], self.action_tiles_load)
        elif sub_action == 'file_picked':
            # Verify the file extension is a supported image type, then open the
            # tile-sheet sizer.
            d = widget
            if d.value is not None:
                file_path = d.value
                # Make sure we have a file.
                if not os.path.isfile(file_path):
                    self.gui_alert('Not a file: '+file_path)
                    return
                ext = os.path.splitext(file_path)[1][1:]
                # Make sure we have an image file type (check extension).
                if ext.lower() not in toolkit.IMAGE_FILE_EXTENSIONS:
                    self.gui_alert('Unsupported image file type: '+ext)
                    return
                # Hand off to the sizer dialog.
                try:
                    self.gui_tilesheet_sizer(file_path, self.action_tiles_load)
                except:
                    pass
        elif sub_action == 'tilesheet_sized':
            d = widget
            values = d.values
            tilesheet = toolkit.Tilesheet(
                d.file_path,
                d.image,
                Vec2d(values[0:2]),
                Vec2d(values[2:4]),
                Vec2d(values[4:6]),
                d.rects,
            )
            self.tilesheets.insert(0, tilesheet)
            self.gui.widget.remove(self.gui_form['side_panel'])
            make_side_panel(self.gui.widget)
            # Save the tilesheet meta data to PATH.tilesheet.
            toolkit.put_tilesheet_info(tilesheet.file_path, values)

    # MapEditor.action_tiles_load
    
    def action_tiles_close(self, * args):
        """Close tiles action: close a tilesheet.
        """
        self.gui_tilesheet_closer()
    
    # MapEditor.action_tiles_close
    
    def action_entities_clear(self, sub_action=None, widget=None):
        """Clear entities action: clear all entities from editor.
        
        This is a reentrant method. The sub_action argument drives the behavior.
        It is called initially by an event handler, and again by GUI callback.
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
                self.deselect()
                del self.mouseover_shapes[:]
                self.changes_unsaved = False
                self.set_entities_file(None)
        
    # MapEditor.action_entities_clear
    
    def action_entities_import(self, sub_action=None, widget=None):
        """Import entities action: load entities from a file.
        
        This is a reentrant method. The sub_action argument drives the behavior.
        It is called initially by an event handler, and again by GUI callback.
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
                    data.paths['map'], self.action_entities_import)
        elif sub_action == 'file_picked':
            d = widget
            if d.value is not None:
                self.set_entities_file(d.value)
                # Clear out the world.
                State.world.remove(*State.world.entity_branch.keys())
                # Run the importer plugin.
                try:
                    file_handle = open(State.file_entities, 'rb')
                    entities,tilesheets = toolkit.import_world_quadtree(
                        file_handle, RectGeom, PolyGeom, CircleGeom)
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
                    State.world.add_list(entities)
                    load_tiles(entities, tilesheets)
                    self.deselect()
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
        # Don't save the mouse shape.
        State.world.remove(self.mouse_shape)
        # Run the exporter plugin.
        try:
            file_handle = open(State.file_entities, 'wb')
            entities = State.world.entity_branch.keys()
            toolkit.export_world_quadtree(file_handle, entities)
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
        
        This is a reentrant method. The sub_action argument drives the behavior.
        It is called initially by an event handler, and again by GUI callback.
        """
        if sub_action is None:
            # Get input file name.
            self.gui_browse_file("Save Entities As",
                data.paths['map'], self.action_entities_save_as)
        elif sub_action == 'file_picked':
            d = widget
            if d.value is not None:
                State.file_entities = d.value
                self.action_entities_save()
    
    def action_quit_app(self, sub_action=None, widget=None):
        """Quit app action.
        
        This is a reentrant method. The sub_action argument drives the behavior.
        It is called initially by an event handler, and again by GUI callback.
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
    
    def action_view_map_grid(self, *args):
        """View grid action: toggle.
        """
        State.show_grid = not State.show_grid
    
    def action_view_map_labels(self, *args):
        """View labels action: toggle labels.
        """
        State.show_labels = not State.show_labels
    
    def action_view_world_grid(self, *args):
        """View world grid action: toggle world's level 1.5 branches grid.
        """
        State.show_world_grid = not State.show_world_grid
    
    def action_view_rects(self, *args):
        """View rects action: toggle rects.
        """
        State.show_rects = not State.show_rects
    
    def action_view_hud(self, *args):
        """View HUD action: toggle HUD.
        """
        State.show_hud = not State.show_hud
    
    def action_view_help(self, *args):
        """View Help action: open a help viewer dialog.
        """
        self.gui_view_text(
            'Gummworld2 World Editor Help',
            HELP_TEXT.split('\n'), width=600, height=300)
    
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
        # key control and user_data input; and other keystrokes if user_data has
        # focus.
        user_data = self.gui_form['user_data']
        if user_data.container.myfocus is user_data:
            if key in (K_ESCAPE,):
                user_data.blur()
                return
            # Filter out keystrokes that are "ugly" in text inputs.
            if key not in (K_DELETE,K_TAB):
                self.gui.event(e)
            return
        elif not self.modal and key == K_RETURN and self.selected is not None:
            user_data.focus()
            return
        # Filter out keystrokes that are "ugly" in text inputs.
        if key not in (K_DELETE,K_TAB):
            self.gui.event(e)
        ## Customization: beware of key conflicts with pgu.gui.
        if not self.modal:
            if key in (K_DELETE,K_KP_PERIOD):
                self.action_shape_delete()
            elif key == K_ESCAPE:
                self.action_quit_app()
            elif key in (K_EQUALS,K_MINUS):
                self.action_key_inflate_shape(key, mod)
            elif key in (K_LEFT,K_RIGHT,K_UP,K_DOWN):
                self.action_key_grab_shape(key, mod)
            elif key == K_c and mod & KMOD_CTRL:
                self.action_shape_copy()
            elif key == K_x and mod & KMOD_CTRL:
                self.action_shape_cut()
            elif key == K_v and mod & KMOD_CTRL:
                self.action_shape_paste()
            elif key == K_TAB:
                GEOM_COLORS.next()
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
        self.gui_modal_off()
        self.gui.screen = State.screen.surface
        self.gui.resize()
        self.remake_scrollbars(reset=False)
        c = self.gui.widget
        side_panel = self.gui_form['side_panel']
        c.remove(side_panel)
        make_side_panel(c)
        self.select(self.selected)
    
    def on_user_event(self, e):
        """Handler for USEREVENT events.
        """
#        print 'USEREVENT',e.dict()
        pass
    
    def on_quit(self):
        """Handler for QUIT events.
        """
        self.action_quit_app()
        
    # MapEditor.on_quit


def tiles_bounding_rect(tiles):
    """Derive the bounding rect for a sequence of tiles.
    """
    if len(tiles):
        rect = tiles[0].tile_rect.copy()
        tw,th = rect.size
        if len(tiles) > 1:
            rect.unionall_ip([t.tile_rect for t in tiles[1:]])
            # Grid-align position.
            nx = rect.x // tw
            ny = rect.y // th
            rect.x = nx * tw
            rect.y = ny * th
            # Remove spacing from width and height.
            maxx = reduce(max, [t.tile_rect.x for t in tiles])
            maxy = reduce(max, [t.tile_rect.y for t in tiles])
            rect.w = rect.w // tw * tw
            rect.h = rect.h // th * th
        return rect
    else:
        return Rect(0,0,1,1)


def load_tiles(entities, tilesheets):
    for entity in entities:
        for line in entity.user_data.split('\n'):
            if line.startswith('tile '):
                parts = line.split(' ')
                name = parts[2]
                tilesheet = tilesheets[name]
                tile_id = int(parts[1])
                info = tilesheet.tile_info(tile_id)
                entity.tiles.append(Tile(
                    info.image, info.name, info.rect,
                    info.tilesheet, info.tile_id))


def draw_tiles(position, tiles, alpha=255):
    """Draw a sequence of tiles centered on position.
    """
    if len(tiles) == 0:
        return
    # Get bounding rect for the sequence of tiles.
    bounding_rect = tiles_bounding_rect(tiles)
    # Calculate offset to argument position.
    move_center = State.camera.world_to_screen(position)
    diff = bounding_rect.center - Vec2d(bounding_rect.topleft)
    # Place individual tiles...
    tw,th = tiles[0].tile_rect.size
    blit = State.screen.blit
    for tile in tiles:
        image = tile.tile_image.copy()
        image.set_alpha(alpha)
        rect = tile.tile_rect.copy()
        # Translate to argument position, removing tile spacing.
        nx = (rect.x-bounding_rect.x) // tw
        ny = (rect.y-bounding_rect.y) // th
        rect.x = (move_center.x - diff.x) + nx * tw
        rect.y = (move_center.y - diff.y) + ny * th
        blit(image, rect)


def make_hud():
    """Create a HUD with dynamic items.
    """
    State.hud = HUD()
    State.hud.x += 20
    State.hud.top += State.hud.font_height * 2
    next_pos = State.hud.next_pos
    
#    State.hud.add('FPS',
#        Statf(next_pos(), 'FPS %d', callback=State.clock.get_fps))
    
    def get_entities_file():
        if State.file_entities:
            return data.relpath(State.file_entities)
        else:
            return 'none'
    State.hud.add('Save File', Statf(next_pos(),
        'Save File %s', callback=get_entities_file, interval=1000) )
    
    rect = State.world.rect
    l,t,r,b = rect.left,rect.top,rect.right,rect.bottom
    State.hud.add('Bounds',
        Stat(next_pos(), 'Bounds %s'%((int(l),int(t),int(r),int(b)),)) )
    
    def get_mouse():
        s = pygame.mouse.get_pos()
        w = State.camera.screen_to_world(s)
        return 'S%s W%s@%s' % (str(s), str((int(w.x),int(w.y),)),
            str(State.world.level_of(State.app.mouse_shape)).lower())
    State.hud.add('Mouse',
        Statf(next_pos(), 'Mouse %s', callback=get_mouse, interval=100))
    
#    def get_world_pos():
#        s = State.camera.world_to_screen(State.camera.position)
#        w = State.camera.position
#        return 'S'+str((int(s.x),int(s.y),)) + ' W'+str((int(w.x),int(w.y),))
#    State.hud.add('Camera',
#        Statf(next_pos(), 'Camera %s', callback=get_world_pos, interval=100))

#    def gui_name():
#        w = State.app.gui_hover()
#        return w.name if w else 'none'
#    State.hud.add('Widget',
#        Statf(next_pos(), 'Widget %s', callback=gui_name, interval=100))
    
    def get_selected():
        shape = State.app.selected
        return 'none' if shape is None else '%s@%d/%d'%(
            shape.rect.center, State.world.level_of(shape), State.world.num_levels)
    State.hud.add('Selected',
        Statf(next_pos(), 'Selected %s', callback=get_selected, interval=100))
    
    def get_top_level():
        n = len(State.world.entities)
        return str(n)
    State.hud.add('In Top Level',
        Statf(next_pos(), 'In Top Level %s', callback=get_top_level, interval=100))

# make_hud


def make_menus(container):
    """Make GUI menus for content control.
    """
    app = State.app
    menus = gui.Menus([
        ('File/Quit',         app.action_quit_app, None),
        ('Entities/Import',   app.action_entities_import, None),
        ('Entities/Save',     app.action_entities_save, None),
        ('Entities/Save As',  app.action_entities_save_as, None),
        ('Entities/Clear',    app.action_entities_clear, None),
        ('Images/New Map',    app.action_map_new, None),
        ('Images/Load Map',   app.action_map_load, None),
        ('Images/Load Tiles', app.action_tiles_load, None),
        ('Images/Close Tiles',app.action_tiles_close, None),
        ('View/Map Grid',     app.action_view_map_grid, None),
        ('View/Map Labels',   app.action_view_map_labels, None),
        ('View/World Grid',   app.action_view_world_grid, None),
        ('View/Shape Rects',  app.action_view_rects, None),
        ('View/HUD',          app.action_view_hud, None),
        ('View/Help',         app.action_view_help, None),
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
    t.td(gui.Tool(g, gui.Label('Pent'), 'pent_tool', height=h))
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
        value='', name='user_data',
        font=smaller_font, width=w, height=5*smaller_font.get_height())
    user_data.connect(gui.CHANGE, State.app.action_set_userdata, user_data)
    t.td(user_data)
    
    # Tile palette: table in a scroll area.
    t.tr()
    t.td(gui.Spacer(1,6), colspan=2)
    t.tr()
    t.td(gui.Label('Tiles:'), colspan=2, align=-1)
    t.tr()
    w = (State.screen.width - State.camera.view.width - 13)
    h = (State.screen.height - t.resize()[1] - 3)
    tile_palette = gui.Document(name='tile_palette')
    
    # Tile palette contents (Document).
    toolbar_group = State.app.gui_form['toolbar_group']
    tile_palette.block(-1)
    for tilesheet in State.app.tilesheets:
        prevy = tilesheet.rects[0].y
        for tile_id,rect in enumerate(tilesheet.rects):
            if rect.y != prevy:
                tile_palette.block(-1)
                prevy = rect.y
            ti = tilesheet.tile_info(tile_id)
            tile = Tile(ti.image, ti.name, ti.rect, tilesheet, tile_id)
            tile.connect(gui.CLICK, State.app.set_stamp,
                tilesheet, rect, tile.value)
            tile_palette.add(tile)
            tile_id += 1
        tile_palette.br(2)
        tile_palette.block(-1)
    
    # Add tile palette to a scroll area, then the panel's table.
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
