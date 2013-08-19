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


__doc__ = """toolkit.py - Some helper tools for Gummworld2.
"""


import os
import re
import urllib


import pygame
from pygame.locals import RLEACCEL, SRCALPHA, BLEND_RGBA_ADD, Color
from pygame.sprite import Sprite

from gummworld2 import data, State, BasicMap, BasicLayer, Vec2d
from gummworld2.geometry import (
    RectGeometry, LineGeometry, PolyGeometry, CircleGeometry,
)
from gummworld2.ui import HUD, Stat, Statf, hud_font
from tiledtmxloader.tmxreader import TileMapParser
from tiledtmxloader.helperspygame import ResourceLoaderPygame


# Filename-matching extensions for image formats that pygame can load.
IMAGE_FILE_EXTENSIONS = (
    'gif','png','jpg','jpeg','bmp','pcx', 'tga', 'tif',
    'lbm', 'pbm', 'pgm', 'xpm',
)


class Struct(object):
    """A class with arbitrary members. Construct it like a dict, then access the
    keys as instance attributes.
    
    s = Struct(x=2, y=4)
    print s.x,s.y
    """
    
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class Tilesheet(object):
    
    def __init__(self, file_path, image, margin, tile_size, spacing, rects):
        self.file_path = file_path
        self.image = image
        self.margin = margin
        self.tile_size = tile_size
        self.spacing = spacing
        self.rects = rects
    
    def get_image(self, tile_id):
        rect = self.rects[tile_id]
        tile = self.image.subsurface(rect).copy()
        return tile
    
    def tile_info(self, tile_id):
        """Return a Struct populated with tilesheet info for tile_id. This info
        represents everything needed by the Tile class constructor in
        world_editor.py.
        
        Struct members:
            name : str; relative path to image file
            image : pygame.surface.Surface; the loaded image
            margin : Vec2d; size of image's edge border
            size : Vec2d; size of a single tile
            spacing : Vec2d; spacing between tiles
            rects : pygame.Rect; list of rects defining tile subsurfaces
        """
        tile = self.get_image(tile_id)
        rect = self.rects[tile_id]
        info = Struct(image=tile, name=self.file_path, rect=rect,
                    tilesheet=self, tile_id=tile_id)
        return info



def make_hud(caption=None, visible=True):
    """Create a HUD with dynamic items. This creates a default hud to serve
    both as an example, and for an early design and debugging convenience.
    """
    State.hud = HUD()
#    State.hud.visible = visible
    next_pos = State.hud.next_pos
    
    if caption:
        State.hud.add('Caption', Stat(next_pos(), caption))
    
    State.hud.add('FPS',
        Statf(next_pos(), 'FPS %d', callback=lambda:State.clock.fps))
    
    rect = State.world.rect
    l,t,r,b = rect.left,rect.top,rect.right,rect.bottom
    State.hud.add('Bounds',
        Stat(next_pos(), 'Bounds %s'%((int(l),int(t),int(r),int(b)),)) )
    
    def get_mouse():
        s = pygame.mouse.get_pos()
        w = State.camera.screen_to_world(s)
        return 'S'+str(s) + ' W'+str((int(w.x),int(w.y),))
    State.hud.add('Mouse',
        Statf(next_pos(), 'Mouse %s', callback=get_mouse, interval=.1))
    
    def get_world_pos():
        s = State.camera.world_to_screen(State.camera.position)
        w = State.camera.position
        return 'S'+str((int(s.x),int(s.y),)) + ' W'+str((int(w.x),int(w.y),))
    State.hud.add('Camera',
        Statf(next_pos(), 'Camera %s', callback=get_world_pos, interval=.1))

# make_hud


def make_tiles(label=False):
    """Create tiles to fill the current map. This is a utility for easily making
    visible content to aid early game design or debugging.
    
    Tiles transition from top-left to bottom-right, red to blue.
    """
    # Tiles are sprites; each sprite must have a name, an image, and a rect.
    tw,th = State.map.tile_width, State.map.tile_height
    mw,mh = State.map.width, State.map.height
    layer = BasicLayer(State.map, 0)
    State.map.layers.append(layer)
    if label:
        font = pygame.font.Font(data.filepath('font', 'Vera.ttf'), 7)
        fg = Color('yellow')
        bg = Color(70,70,70)
    for y in range(mh):
        for x in range(mw):
            s = pygame.sprite.Sprite()
            s.name = (x,y)
            s.image = pygame.surface.Surface((tw,th))
            facx = max(float(x) / mw, 0.01)
            facy = max(float(y) / mh, 0.01)
            R = 255-255*facx
            G = 0
            B = 255*facy
            s.image.fill((R,G,B))
            s.rect = s.image.get_rect(topleft=(x*tw,y*th))
            if label:
                tag = font.render(str(s.name), 1, fg, bg)
                s.image.blit(tag, (1,1))
            layer.add(s)

# make_tiles


def make_tiles2():
    """Create tiles to fill the current map. This is a utility for easily making
    visible content to aid early game design or debugging.
    
    Tiles transition from top to bottom, light blue to brown.
    """
    # Tiles are sprites; each sprite must have a name, an image, and a rect.
    tw,th = State.map.tile_width, State.map.tile_height
    mw,mh = State.map.width, State.map.height
    layer = BasicLayer(State.map, 0)
    State.map.layers.append(layer)
    for y in range(mh):
        for x in range(mw):
            s = pygame.sprite.Sprite()
            s.name = (x,y)
            s.image = pygame.surface.Surface((tw,th))
            facy = max(float(y) / mh, 0.01)
            R = 200-100*facy
            G = 150-100*facy
            B = 249-249*facy
            s.image.fill((R,G,B))
            pygame.draw.line(s.image, (R+9,G+9,B+9), (0,0), (0,th))
            s.rect = s.image.get_rect(topleft=(x*tw,y*th))
            layer.add(s)

# make_tiles2


def load_entities(filepath, cls_dict={}):
    """Load entities via import_world() plugin.
    
    The cls_dict argument is a dict of classes to construct when encountering
    shape data. The following keys are supported: 'rect_cls', 'line_cls',
    'poly_cls', 'circle_cls'. If any of those keys are missing from cls_dict,
    the following classes will be used by default: geometry.RectGeometry,
    geometry.LineGeometry, geometry.PolyGeometry, geometry.CircleGeometry.
    Classes substituted in this manner must have constructors that are
    compatible with the default classes.
    """
    file_handle = open(filepath, 'rb')
    entities,tilesheets = import_world(file_handle, **cls_dict)
    file_handle.close()
    return entities,tilesheets

# load_world


def export_world(fh, entities):
    """A sequence-to-text exporter.
    
    This function is required by world_editor.py, and possibly other scripts, to
    export entities to a text file.
    
    Geometry classes used by this plugin are: RectGeometry, CircleGeometry, and
    PolyGeometry.
    
    The values saved are those needed for each shape-class's constructor, plus a
    block of arbitrary user data. The user data is url-encoded.
    """
    
    if not isinstance(entities, (list,tuple)) and not hasattr(entities, '__iter__'):
        raise pygame.error, 'entities must be iterable'
    
    def quote(user_data):
        translated_data = []
        for line in user_data.split('\n'):
            line = line.rstrip('\r')
            line = re.sub(r'\\', '/', line)
            translated_data.append(line)
        quoted_data = '\n'.join(translated_data)
        quoted_data = urllib.quote(quoted_data)
        return quoted_data
    
    for entity in entities:
        if isinstance(entity, RectGeometry):
            # format:
            # rect x y w h
            # user_data ...
            x,y = entity.rect.topleft
            w,h = entity.rect.size
            user_data = ''
            if hasattr(entity, 'user_data'):
                user_data = quote(entity.user_data)
            fh.write('rect %d %d %d %d\n' % (x, y, w, h))
            fh.write('user_data ' + user_data + '\n')
        elif isinstance(entity, LineGeometry):
            # format:
            # rect x y w h
            # user_data ...
            x1,y1 = entity.p1
            x2,y2 = entity.p2
            posx,posy = entity.position
            user_data = ''
            if hasattr(entity, 'user_data'):
                user_data = quote(entity.user_data)
            fh.write('line %d %d %d %d %d %d\n' % (x1,y1, x2,y2, posx,posy))
            fh.write('user_data ' + user_data + '\n')
        elif isinstance(entity, CircleGeometry):
            # format:
            # circle centerx centery radius
            # user_data ...
            x,y = entity.position
            radius = entity.radius
            user_data = ''
            if hasattr(entity, 'user_data'):
                user_data = quote(entity.user_data)
            fh.write('circle %d %d %d\n' % (x,y,radius))
            fh.write('user_data ' + user_data + '\n')
        elif isinstance(entity, PolyGeometry):
            # format:
            # poly centerx centery rel_x1 rel_y1 rel_x2 rel_y2 rel_x3 rel_y3...
            # user_data ...
            #
            # Note: x and y are relative to the containing rect's topleft.
            center = entity.rect.center
            x,y = entity.rect.topleft
            w,h = entity.rect.size
            user_data = ''
            if hasattr(entity, 'user_data'):
                user_data = quote(entity.user_data)
            fh.write('poly')
            fh.write(' %d %d' % center)
            for x1,y1 in entity.points:
                fh.write(' %d %d' % (x1-x,y1-y))
            fh.write('\n')
            fh.write('user_data ' + user_data + '\n')
        else:
            raise pygame.error, 'unsupported type: ' + entity.__class__.__name__
    
# export_world


def import_world(
        fh, rect_cls=RectGeometry, line_cls=LineGeometry,
        poly_cls=PolyGeometry, circle_cls=CircleGeometry):
    """A world entity importer.
    
    This function is required by world_editor.py, and possibly other scripts, to
    import world entities from a text file. It understands the format of files
    created by export_world().
    
    Geometry classes used by this function to create shape objects are specified
    by the rect_cls, line_cls, poly_cls, and circle_cls arguments. The
    constructor parameters must have the same signature as geometry.RectGeometry,
    et al.
    
    The values imported are those needed for each shape-class's constructor,
    plus a block of arbitrary user data which will be placed in the shape
    instance's user_data attribute.
    
    The user_data is also parsed for tilesheet info. Tilesets are loaded and
    returned as a dict of toolkit.Tilesheet, keyed by relative path to the
    image file.
    """
    
    if not issubclass(rect_cls, RectGeometry):
        raise pygame.error, 'argument "rect_cls" must be a subclass of geometry.RectGeometry'
    if not issubclass(line_cls, LineGeometry):
        raise pygame.error, 'argument "line_cls" must be a subclass of geometry.LineGeometry'
    if not issubclass(poly_cls, PolyGeometry):
        raise pygame.error, 'argument "poly_cls" must be a subclass of geometry.PolyGeometry'
    if not issubclass(circle_cls, CircleGeometry):
        raise pygame.error, 'argument "circle_cls" must be a subclass of geometry.CircleGeometry'
    
    entities = []
    tilesheets = {}
    
    line_num = 0
    for line in fh:
        line_num += 1
        line = line.rstrip('\r\n')
        parts = line.split(' ')
        if len(parts) < 1:
            continue
        what = parts[0]
        if what == 'user_data':
            # User data format:
            # user_data url_encoded_string
            user_data = []
            # Unquote the user_data string and split it into lines.
            lines = urllib.unquote(' '.join(parts[1:])).split('\n')
            # Scan each line for tile info, load the tilesheets, and populate the
            # entity's user_data attribute.
            for line in lines:
                # Split into space-delimited tokens.
                parts = line.split(' ')
                if parts[0] == 'tile':
                    # Process the tile info entry. Format is:
                    # 0: tile
                    # 1: tile_id
                    # 2..end: relpath_of_image
                    file_path = ' '.join(parts[2:])
                    file_path = os.path.join(*file_path.split('/'))
                    if file_path not in tilesheets:
                        tilesheet = load_tilesheet(file_path)
                        tilesheets[file_path] = tilesheet
                    # Join the parts and append to user_data.
                    line = ' '.join(parts[0:2] + [file_path])
                user_data.append(line)
            entity.user_data = '\n'.join(user_data)
        elif what == 'rect':
            # Rect format:
            # rect x y w h
            x,y = int(parts[1]), int(parts[2])
            w,h = int(parts[3]), int(parts[4])
            entity = rect_cls(x, y, w, h)
            entities.append(entity)
        elif what == 'line':
            # Line format:
            # line x1 y1 x2 y2 posx posy
            x1,y1 = int(parts[1]), int(parts[2])
            x2,y2 = int(parts[3]), int(parts[4])
            pos = int(parts[5]), int(parts[6])
            entity = line_cls(x1, y1, x2, y2, pos)
            entities.append(entity)
        elif what == 'circle':
            # Circle format:
            # circle centerx centery radius
            x,y = int(parts[1]), int(parts[2])
            radius = float(parts[3])
            entity = circle_cls((x,y), radius)
            entities.append(entity)
        elif what == 'poly':
            # Polygon format:
            # poly centerx centery rel_x1 rel_y1 rel_x2 rel_y2 rel_x3 rel_y3...
            #
            # Note: x and y are relative to the containing rect's topleft.
            center = int(parts[1]), int(parts[2])
            points = []
            for i in range(3, len(parts), 2):
                points.append(( int(parts[i]), int(parts[i+1]) ))
            entity = poly_cls(points, center)
            entities.append(entity)
        else:
            raise pygame.error, 'line %d: keyword "%s" unexpected' % (line_num,what)
        
    return entities, tilesheets
    
# import_world
    

def load_tilesheet(file_path):
    """Load a tilesheet. A toolkit.Tilesheet containing tilesheet info is
    returned.
    
    The file_path argument is the path to the image file. If file_path is a
    relative path, it must exist relative to data.data_dir (see the
    gummworld2.data module). If file_path.tilesheet exists it will be used to
    size the tiles; otherwise the defaults (0,0,32,32,0,0) will be used.
    """
    # Make sure we have an image file type (check file extension).
    if not os.path.isabs(file_path):
        file_path = os.path.join(data.data_dir,file_path)
    junk,ext = os.path.splitext(file_path)
    ext = ext.lstrip('.')
    if ext.lower() not in IMAGE_FILE_EXTENSIONS:
        self.gui_alert('Unsupported image file type: '+ext)
        return
    # Load the image and tilesheet dimensions.
    image = pygame.image.load(file_path)
    values = [int(s) for s in get_tilesheet_info(file_path)]
    margin = Vec2d(values[0:2])
    tile_size = Vec2d(values[2:4])
    spacing = Vec2d(values[4:6])
    rects = []
    # Carve up the tile sheet, working in margin and spacing offsets.
    w,h = image.get_size()
    tx,ty = tile_size
    mx,my = margin
    sx,sy = spacing
    nx,ny = w//tx, h//ty
    for y in range(ny):
        for x in range(nx):
            rx = mx + x * (tx + sx)
            ry = my + y * (ty + sy)
            rects.append(pygame.Rect(rx,ry,tx,ty))
    # Make a tilesheet.
    tilesheet = Tilesheet(file_path, image, margin, tile_size, spacing, rects)
    return tilesheet


def get_tilesheet_info(tilesheet_path):
    """Get the tilesheet meta data from file if it exists.
    """
    meta_file = tilesheet_path + '.tilesheet'
    values = ['0','0','32','32','0','0']
    try:
        f = open(meta_file)
        line = f.read().strip('\r\n')
        parts = line.split(' ')
        if len(parts) == 6:
            values[:] = parts
    except:
        pass
    else:
        f.close()
    return values


def put_tilesheet_info(tilesheet_path, tilesheet_values):
    """Put the tilesheet meta data to file.
    """
    meta_file = tilesheet_path + '.tilesheet'
    try:
        f = open(meta_file, 'wb')
        f.write(' '.join([str(v) for v in tilesheet_values]) + '\n')
    except:
        pass
    else:
        f.close()


def get_visible_cell_ids(camera, map_, max_speed=10):
    """Return a list of the map's cell IDs that would be visible to the camera.
    This function is mainly for SuperMap, which needs to specify the map.
    
    The camera argument is the camera that defines the view.
    
    The map_ argument is the BasicMap or TiledMap to query.
    
    The max_speed argument adds this many pixels to each edge of the query rect
    to accommodate for the space moved during frame interpolation cycles. This
    should at least match the scrolling speed to avoid black flickers at the
    screen edge.
    
    The return value is a list of cell IDs in the map's spatialhash for each
    layer. The per-layer values are necessary because maps can have layers with
    different tile sizes, and therefore different grids.
    
    The return value is suitable for passing to get_objects_in_cell_ids().
    
    Returns:
        [   [cell_id0, cell_id1, ...],  # layer0
            [cell_id0, cell_id1, ...],  # layer1
            ...,                        # layerN
        ]
    """
    empty_list = []
    cell_ids = []
    query_rect = camera.rect.inflate(max_speed*2,max_speed*2)
    for layer in map_.layers:
        if layer.visible:
            cell_ids.append(layer.objects.intersect_indices(query_rect))
        else:
            cell_ids.append(empty_list)
    return cell_ids


def get_objects_in_cell_ids(map_, cell_ids_per_layer):
    """Return a list of objects per layer for the specified cell IDs.
    This function is mainly for SuperMap, which needs to specify the map.
    
    The argument cell_ids_per_layer is a list of nested lists containing
    cell IDs:
        [   [cell_id0, cell_id1, ...],  # layer0
            [cell_id0, cell_id1, ...],  # layer1
            ...,                        # layerN
        ]
    
    The return value is a similary constructed list of object lists:
        [   [obj0, obj1, ...],          # layer0
            [obj0, obj1, ...],          # layer1
            ...,                        # layerN
        ]
    """
    objects_per_layer = []
    for layeri,cell_ids in enumerate(cell_ids_per_layer):
        get_cell = map_.layers[layeri].objects.get_cell
        objects = set()
        objects_update = objects.update
        for cell_id in cell_ids:
            objects_update(get_cell(cell_id))
        objects_per_layer.append(list(objects))
    return objects_per_layer


def get_object_array(max_speed=10):
    """Return a list of the map's objects that would be visible to the camera.
    Operates on State.map and State.camera.
    
    The max_speed argument adds this many pixels to each edge of the query rect
    to accommodate for the space moved during frame interpolation cycles. This
    should at least match the scrolling speed to avoid black flickers at the
    screen edges.
    
    The return value is a list of object lists:
        [   [obj0, obj1, ...],          # layer0
            [obj0, obj1, ...],          # layer1
            ...,                        # layerN
        ]
    """
    objects_per_layer = []
    empty_list = []
    query_rect = State.camera.rect.inflate(max_speed*2,max_speed*2)
    for layer in State.map.layers:
        if layer.visible:
            objects_per_layer.append(
                layer.objects.intersect_objects(query_rect))
        else:
            objects_per_layer.append(empty_list)
    return objects_per_layer


def draw_object_array(object_array):
    """Draw a layered array of objects.
    
    For best performance:
        
    def update(self, dt):
        self.visible_objects = toolkit.get_object_array()
    def draw(self, dt):
        ...
        toolkit.draw_object_array(self.visible_objects)
    """
    cam = State.camera
    blit = cam.view.blit
    cx,cy = cam.rect.topleft
    for sprites in object_array:
        for sprite in sprites:
            if not sprite.image:
                continue
            rect = sprite.rect
            sx,sy = rect.topleft
            blit(sprite.image, (sx-cx,sy-cy))


def draw_sprite(s, blit_flags=0):
    """Draw a sprite on the camera's surface using world-to-screen conversion.
    """
    camera = State.camera
    cx,cy = camera.rect.topleft
    sx,sy = s.rect.topleft
    camera.surface.blit(s.image, (sx-cx, sy-cy), None, blit_flags)

# draw_sprite


def draw_tiles():
    """Draw visible tiles.
    
    Quick and dirty draw function, handles getting the objects and drawing
    them. This is a bit more expensive than getting tiles during the update
    cycle and reusing the object array for the draw cycles. However, it is
    less hassle, and one might want to use this tactic if panning more than
    one tile span per tick.
    """
    map_ = State.map
    camera = State.camera
    blit = camera.surface.blit
    cx,cy = camera.rect.topleft
    visible_cell_ids = get_visible_cell_ids(camera, map_)
    visible_objects = get_objects_in_cell_ids(map_, visible_cell_ids)
    for sprites in visible_objects:
        for sprite in sprites:
            rect = sprite.rect
            sx,sy = rect.topleft
            blit(sprite.image, (sx-cx,sy-cy))

# draw_tiles


def interpolated_step(pos, step, interp):
    """Returns (float,float).
    
    This is a utility for drawing routines, after pos has been updated by step.
    For example:
        def update():
            move_camera()
            State.camera.update()
            sprite_group.update()  # e.g. steps a sprite position
        def draw():
            interp = State.camera.interpolate()
            camera_pos = State.camera.rect.topleft
            for s in sprite_group:
                sprite_pos = Vec2d(s.rect.topleft)
                pos = sprite_pos - camera_pos
                step = s.step
                interp_pos = toolkit.interpolated_step(pos, step, interp)
                surf.blit(s.image, interp_pos)
    """
    # Interpolated step = step * interpolation factor
    interp_step = Vec2d(step) * interp
    
    # Interpolated pos = screen_pos - step + interpolated step
    x,y = pos
    pos = float(x),float(y)
    return pos - step + interp_step

# interpolated_step


## EXPERIMENTAL: not working quite right
#def get_parallax_tile_range(cam, map, layer, parallax, orig='bottomleft'):
def get_parallax_tile_range(cam, map, layer, parallax, orig='center'):
    # Compute the camera center for this layer's parallax.
    mapw,maph = Vec2d(layer.width,layer.height)
    tile_size = Vec2d(layer.tile_width,layer.tile_height)
    map_off = map.rect.topleft
    cam_rect = pygame.Rect(cam.rect)
    map_orig = Vec2d(getattr(map.rect, orig))
    cam_orig = Vec2d(getattr(cam_rect, orig))
    distance = (cam_orig - map_orig) * parallax
    setattr(cam_rect, orig, map_orig+distance)
    # Get the visible tile range.
    left,top = (cam_rect.topleft-tile_size-map_off) // tile_size
    right,bottom = (cam_rect.bottomright+tile_size-map_off) // tile_size
    if left < 0: left = 0
    if top < 0: top = 0
    if right > mapw: right = mapw
    if bottom > maph: bottom = maph
    return (left,top,right,bottom),cam_rect


## EXPERIMENTAL: not working quite right
def draw_parallax_tile_range(layer, tile_range, pax_rect):
#    tiles = layer.get_tiles(*tile_range)
    x,y,r,b = tile_range
    tw,th = layer.tile_width,layer.tile_height
    query_rect = pygame.Rect(x*tw, y*th, (r-x)*tw, (b-y)*th)
##    print query_rect;quit()
    tiles = layer.get_objects_in_rect(query_rect)
    X_draw_parallax_tiles(layer, tiles, pax_rect)


## EXPERIMENTAL: not working quite right
def X_draw_parallax_tiles(layer, tiles, pax_rect, view=None):
    ## DEPRECATED
    parallax_cam_topleft = Vec2d(pax_rect.topleft)
    if not view:
        view = State.camera
    blit = view.surface.blit
    abs_offset = Vec2d(view.abs_offset)
    for s in tiles:
        if s:
            r = pygame.Rect(s.rect)
            r.center -= parallax_cam_topleft
            blit(s.image, r.topleft-abs_offset)


## EXPERIMENTAL: not working quite right
def draw_parallax_tiles(maps, view):
    """maps is a list of maps
    
    Assumptions:
        1. Maps are in world coords.
        2. Each map has the same number of layers.
        3. Each map's corresponding layer has the same parallax value.
        4. Each map layer has a parallax attribute: tuple of length 2.
        5. Each map layer has a tile_range attribute: range of visible tiles.
    """
    for i in range(len(maps[0].layers)):
        drawn = {}
        for map in maps:
            layer = map.layers[i]
            tile_size = layer.tile_size
            x1,y1,x2,y2 = layer.tile_range
            pax_rect = layer.parallax_rect
            parallax_cam_topleft = Vec2d(pax_rect.topleft)
            blit = view.blit
            abs_offset = Vec2d(view.abs_offset)
            for y in range(y1,y2):
                for x in range(x1,x2):
                    tile = layer.get_tile_at(x,y)
                    if not tile:
                        continue
                    r = pygame.Rect(tile.rect)
                    r.center -= parallax_cam_topleft - abs_offset
                    pos = tuple(r.topleft // tile_size)
                    if pos in drawn:
                        continue
                    drawn[pos] = 1
                    blit(tile.image, r.topleft)


## EXPERIMENTAL: not working quite right
def draw_parallax_tiles_of_layer(cam, map, layer, parallax=(1.0,1.0)):
    if layer.visible:
        tile_range,pax_rect = get_parallax_tile_range(cam, map, layer, parallax)
        draw_parallax_tile_range(layer, tile_range, pax_rect)



## This is the version used in Fractured Soul.
def draw_tiles_of_layer(layeri, pallax_factor_x=1.0, pallax_factor_y=1.0):
    """Draw visible tiles.
    
    This function assumes that the tiles stored in the map are sprites.
    """
    if layeri < len(State.map.layers):
        layer = State.map.layers[layeri]
        if not layer.visible:
            return
        camera = State.camera
        visible_tile_range = camera.visible_tile_range
        blit = camera.surface.blit
        cx,cy = camera.rect.topleft
        mapw,maph = layer.map_size
        if pallax_factor_x == 1.0 and pallax_factor_y == 1.0:
            left,top,right,bottom = visible_tile_range[layeri]
        else:
            left,top,right,bottom = 0, 0, mapw, maph
        if left < 0: left = 0
        if top < 0: top = 0
        if right >= mapw: right = mapw #- 1
        if bottom >= maph: bottom = maph #- 1
        for y in range(top,bottom):
            yoff = y * mapw
            start = yoff + left
            end = yoff + right
            for s in layer[start:end]:
                if s:
                    rect = s.rect
                    blit(s.image, (rect.x - (cx * pallax_factor_x), rect.y - (cy * pallax_factor_y)))
    else:
        if __debug__ and hasattr(State, 'silence_draw_tiles'):
            print "ERROR: layer", layeri, "not defined int map!"


## These no longer work. Labels and grid lines have been removed from the map
## and layer classes.
##
#def draw_labels(layer=0):
#    """Draw visible labels if enabled.
#    
#    Labels for the specified layer are blitted to the camera surface. If the
#    layer has been collapsed with the collapse_map_layer() function so that
#    the layer's tile size differs from the grid label sprites, this will look
#    weird.
#    """
#    if State.show_labels:
#        tile_range = State.camera.visible_tile_range
#        if len(tile_range):
#            x1,y1,x2,y2 = tile_range[layer]
#            map_layer = State.map.layers[layer]
#            get = map_layer.get_labels
#            for s in get(x1,y1,x2,y2):
#                draw_sprite(s)
#


#def draw_labels(cache_dict, layeri=0, color=pygame.Color('black')):
#    global label_font
#    if label_font is None:
#        label_font = pygame.font.Font(data.filepath('font','Vera.ttf'), 7)
#    lfont = label_font
#    #
#    camera = State.camera
#    cam_rect = State.camera.rect
#    blit = camera.surface.blit
#    left,top,width,height = cam_rect
#    layer = State.map.layers[layeri]
#    tw,th = layer.tile_width, layer.tile_height
#    x0 = left // tw
#    y0 = top // th
#    x1 = tw - (left - x0*tw)
#    y1 = th - (top - y0*th)
###    print x0,y0,x1,y1
#    #
#    for x in xrange(x1, width, layer.tile_width):
#        for y in xrange(y1, height, layer.tile_height):
###            print x,y
#            name = (x+tw)//tw+x0, (y+th)//th+y0
###            name = (x+tw)//tw, (y+th)//th
#            label = cache_dict.get(name, None)
#            if not label:
#                label = lfont.render(str(name), True, color)
#                cache_dict[name] = label
#            blit(label, (x+2,y+2))
def draw_labels(cache_dict, layeri=0, color=pygame.Color('black')):
    global label_font
    if label_font is None:
        label_font = pygame.font.Font(data.filepath('font','Vera.ttf'), 7)
    lfont = label_font
    #
    camera = State.camera
    cam_rect = State.camera.rect
    blit = camera.surface.blit
    left,top,width,height = cam_rect
    layer = State.map.layers[layeri]
    tw,th = layer.tile_width, layer.tile_height
    #
    x1 = tw - (left - left//tw*tw)
    y1 = th - (top - top//th*th)
    #
    for x in xrange(left-tw, left+width+tw, tw):
        for y in xrange(top-th, top+height+th, th):
            name = (x-tw)//tw+1, (y-th)//th+1
            sx,sy = x-left-tw, y-top-th
            label = cache_dict.get(name, None)
            if not label:
                label = lfont.render(
                    '{0[0]:d},{0[1]:d}'.format(name), True, color)
                cache_dict[name] = label
            blit(label, (sx+x1+2,sy+y1+2))
##    quit()
label_font = None

# draw_labels


def draw_grid(grid_cache, layeri=0, color=pygame.Color('blue'), alpha=33):
    """Draw a grid over the camera view.
    
    The grid_lines argument is a list of length two containing a cached
    [vline,hline] pair. This function will initialize the contents if the
    starting values evaluate to False (e.g. [0,0]).
    
    The layeri argument is the map layer from which to get the grid spacing.
    
    The color argument is the desired grid color.
    
    The alpha argument is the surface alpha. If alpha is not None, it must be a
    valid value for pygame.Surface.set_alpha().
    
    color and alpha are only used when when creating the surfaces for the
    grid_lines list.
    """
    camera = State.camera
    cam_rect = State.camera.rect
    blit = camera.surface.blit
    left,top,width,height = cam_rect
    #
    if not grid_cache:
        for name,size in (('vline',(1,height)), ('hline',(width,1))):
            surf = pygame.Surface(size)
            surf.fill(color)
            if alpha is not None:
                surf.set_alpha(alpha)
            grid_cache[name] = surf
    vline = grid_cache.get('vline', None)
    hline = grid_cache.get('hline', None)
    #
    layer = State.map.layers[layeri]
    x1 = layer.tile_width - (left - left // layer.tile_width * layer.tile_width)
    for x in xrange(x1, width, layer.tile_width):
        blit(vline, (x,0))
    y1 = layer.tile_height - (top - top // layer.tile_height * layer.tile_height)
    for y in xrange(y1, height, layer.tile_height):
        blit(hline, (0,y))

# draw_grid
