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


__doc__ = """toolkit.py - Some helper tools for Gummworld2.
"""


import os
import re
import urllib


import pygame
from pygame.locals import RLEACCEL, SRCALPHA, BLEND_RGBA_ADD
from pygame.sprite import Sprite

from gummworld2 import data, State, Map, MapLayer, Vec2d
from gummworld2.geometry import RectGeometry, PolyGeometry, CircleGeometry
from gummworld2.ui import HUD, Stat, Statf, hud_font
from tiledtmxloader import TileMapParser, ImageLoaderPygame

# HACK by Cosmo to get pygame 1.8 working
haspygame19 = pygame.version.vernum >= (1, 9)

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
    State.show_hud = visible
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
        Statf(next_pos(), 'Mouse %s', callback=get_mouse, interval=.1))
    
    def get_world_pos():
        s = State.camera.world_to_screen(State.camera.position)
        w = State.camera.position
        return 'S'+str((int(s.x),int(s.y),)) + ' W'+str((int(w.x),int(w.y),))
    State.hud.add('Camera',
        Statf(next_pos(), 'Camera %s', callback=get_world_pos, interval=.1))

# make_hud


def make_tiles():
    """Create tiles to fill the current map. This is a utility for easily making
    visible content to aid early game design or debugging.
    
    Tiles transition from top-left to bottom-right, red to blue.
    """
    # Tiles are sprites; each sprite must have a name, an image, and a rect.
    tw,th = State.map.tile_size
    mw,mh = State.map.map_size
    State.map.layers.append(MapLayer(
        State.map.tile_size, State.map.map_size, True, True, True))
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
            State.map.add(s)

# make_tiles


def make_tiles2():
    """Create tiles to fill the current map. This is a utility for easily making
    visible content to aid early game design or debugging.
    
    Tiles transition from top to bottom, light blue to brown.
    """
    # Tiles are sprites; each sprite must have a name, an image, and a rect.
    tw,th = State.map.tile_size
    mw,mh = State.map.map_size
    State.map.layers.append(MapLayer(
        State.map.tile_size, State.map.map_size, True, True, True))
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
            State.map.add(s)

# make_tiles2


# def collapse_map(map, num_tiles=(2,2)):
    # """Collapse all layers in a map by combining num_tiles into one tile.
    # Returns a new map.
    
    # The map argument is the source map. It must be an instance of Map.
    
    # The num_tiles argument is a tuple representing the number of tiles in the X
    # and Y axes to combine.
    # """
    # # new map dimensions
    # num_tiles = Vec2d(num_tiles)
    # tw,th = map.tile_size * num_tiles
    # mw,mh = map.map_size // num_tiles
    # if mw * num_tiles.x != map.map_size.x:
        # mw += 1
    # if mh * num_tiles.y != map.map_size.y:
        # mh += 1
    # # new map
    # new_map = Map((tw,th), (mw,mh))
    # # collapse the tiles in each layer...
    # for layeri,layer in enumerate(map.layers):
        # new_layer = collapse_map_layer(map, layeri, num_tiles)
        # # add a new layer
        # new_map.layers.append(new_layer)
    # if hasattr(map, 'tiled_map'):
        # new_map.tiled_map = map.tiled_map
    # return new_map
def collapse_map(map, num_tiles=(2,2), layers=None):
    """Collapse all layers in a map by combining num_tiles into one tile.
    Returns a new map.
    
    The map argument is the source map. It must be an instance of Map.
    
    The num_tiles argument is a tuple representing the number of tiles in the X
    and Y axes to combine.
    """
    # new map dimensions
    num_tiles = Vec2d(num_tiles)
    tw,th = map.tile_size * num_tiles
    mw,mh = map.map_size // num_tiles
    if mw * num_tiles.x != map.map_size.x:
        mw += 1
    if mh * num_tiles.y != map.map_size.y:
        mh += 1
    # new map
    new_map = Map((tw,th), (mw,mh))
    # collapse the tiles in each layer...
    if layers is None:
        layers = range(len(map.layers))
    for layeri in layers:
        layer = map.layers[layeri]
        new_layer = collapse_map_layer(map, layeri, num_tiles)
        # add a new layer
        new_map.layers.append(new_layer)
    if hasattr(map, 'tiled_map'):
        new_map.tiled_map = map.tiled_map
    return new_map

# collapse_map


def collapse_map_layer(map, layeri, num_tiles=(2,2)):
    """Collapse a single layer in a map by combining num_tiles into one tile.
    
    The map argument is the source map. It must be an instance of Map.
    
    The layeri argument is an int representing the layer index to collapse.
    
    The num_tiles argument is a tuple representing the number of tiles in the X
    and Y axes to combine.
    """
    # New map dimensions.
    num_tiles = Vec2d(num_tiles)
    tw,th = map.tile_size * num_tiles
    mw,mh = map.map_size // num_tiles
    if mw * num_tiles.x != map.map_size.x:
        mw += 1
    if mh * num_tiles.y != map.map_size.y:
        mh += 1
    layer = map.layers[layeri]
    new_layer = MapLayer((tw,th), (mw,mh), visible=layer.visible,
        make_grid=True, make_labels=True, name=layer.name)
    # Walk the old map, stepping by the number of the tiles argument...
    for y in range(0, map.map_size.y, num_tiles.y):
        for x in range(0, map.map_size.x, num_tiles.x):
        # Make a new sprite.
            s = Sprite()
            s.image = pygame.surface.Surface((tw,th))
            s.rect = s.image.get_rect()
            s.name = tuple((x,y) / num_tiles)
            
            # Blit (x,y) tile and neighboring tiles to right and lower...
            tiles = map.get_tiles(x, y, x+num_tiles.x, y+num_tiles.y, layer=layeri)
            tiles = [t for t in tiles if t]
            if len(tiles):
                # Detect colorkey.
                colorkey = None
                for tile in tiles:
                    c = tile.image.get_colorkey()
                    if c is not None:
                        colorkey = c
                # Fill dest image if there is a colorkey.
                if colorkey is None and len(tiles) < num_tiles.x*num_tiles.y:
                    colorkey = (0,0,0)
                    s.image.fill(colorkey)
                # Blit the images (first turning off source colorkey).
                for tile in tiles:
                    nx,ny = Vec2d(tile.name) - (x,y)
                    p = s.rect.topleft + map.tile_size * (nx,ny)
                    copy_image = tile.image.copy()
                    copy_image.set_colorkey(None)
                    s.image.blit(copy_image, p)
                # Set the dest colorkey.
                if colorkey is not None:
                    s.image.set_colorkey(colorkey, RLEACCEL)
##                    s.image.set_alpha(tile.image.get_alpha())
                s.rect.topleft = Vec2d(x,y) * map.tile_size
#                if not s.image in map.subpixel_cache:
#                    map.subpixel_cache[s.image] = SubPixelSurface(s.image, 4)
#                s.subpixel_image = map.subpixel_cache[s.image]
                new_layer.append(s)
            else:
                new_layer.append(None)
    
    return new_layer

# collapse_map_layer


def reduce_map_layers(map, layersi):
    """Reduce the number of layers in a map by blitting two or more layers into
    a single layer. A new instance of Map is returned.
    
    The map argument is the source map. It must be an instance of Map.
    
    The layersi argument is a sequence of int of length two or more. The
    layers are blitted in the order specified. Layers not specified and layers
    that are not visible (i.e. layer.visible==False) will be copied as a layer
    instead of being blitted.
    
    Tiles in the blitted layers typically need to have some transparent pixels
    (e.g. a surface colorkey), otherwise their pixels would completely erase the
    tiles underneath.
    
    Alphas and blending are not supported by this routine.
    
    The tile and map sizes in the map layers should be of the same size.
    Otherwise the desired results will likely not be produced. If using
    collapse_map_layer and reduce_map_layers on subsets of map layers, one
    would usually want to call reduce_map_layers first. See the Combo example
    below, in which only two of three layers are transformed.
    
    Yes, this could be a challenge to manage for maps with special-purpose
    layers. One needs to know one's maps and layers before and after the
    transformations. Annotating map layers with a name or ID attribute might
    help. If the base layer has a name attribute it will be copied to the new
    map layer.
    
    Basic example:
        new_map = reduce_map_layers(orig_map, range(len(orig_map.layers)))
    
    Combo example:
        # Reduce 3-layer map to two layers.
        map = reduce_map_layers(map, (0,1))
        # Collapse layer 0, two tiles into one tile.
        map = collapse_map_layer(map, 0, (2,2))
        # The resulting map has two layers numbered 0 and 1.
    """
    # Prepare a new map.
    tw,th = map.tile_size
    mw,mh = map.map_size
    new_map = Map((tw,th), (mw,mh))
    # Prepare a base layer.
    i = layersi[0]
    base_layer = map.layers[i]
    new_base_layer = MapLayer(base_layer.tile_size, base_layer.map_size, visible=base_layer.visible,
        make_grid=True, make_labels=True, name=base_layer.name)
    new_map.layers.append(new_base_layer)
    # Make the base layer.
    for src_sprite in base_layer:
        if src_sprite:
            s = pygame.sprite.Sprite()
            s.image = src_sprite.image.copy()
            s.rect = src_sprite.rect.copy()
            s.name = src_sprite.name
        else:
            s = None
        new_base_layer.append(s)
    # Blit the tiles in the specified layers.
    for layeri in layersi[1:]:
        layer = map.layers[layeri]
        if not layer.visible:
            # Skip invisible layers.
            continue
        for i,src_sprite in enumerate(layer):
            if src_sprite:
                x,y = src_sprite.name
                s = new_base_layer.get_tile_at(x, y)
                if s is None:
                    s = pygame.sprite.Sprite()
                    s.name = x,y
                    s.image = src_sprite.image.copy()
                    s.rect = src_sprite.rect.copy()
                    new_base_layer[i] = s
                else:
                    s.image.blit(src_sprite.image, (0,0))
    # Copy layers that were not specified and layers that are not invisible.
    for i,layer in enumerate(map.layers):
        if i in layersi and layer.visible:
            # Already been copied.
            continue
        new_layer = MapLayer(layer.tile_size, layer.map_size,
            visible=layer.visible, make_grid=True, make_labels=True,
            name=layer.name)
        new_map.insert(i, new_layer)
        for src_sprite in layer:
            if src_sprite:
                s = pygame.sprite.Sprite()
                s.name = src_sprite.name
                s.image = src_sprite.image.copy()
                s.rect = src_sprite.rect.copy()
            else:
                s = None
            new_layer.append(s)
    
    return new_map

# reduce_map_layers


def load_tiled_tmx_map(map_file_name, load_invisible=False, convert_alpha=False):
    """Load an orthogonal TMX map file that was created by the Tiled Map Editor.
    
    Note: convert_alpha is experimental. It can lower performance when used
    with some images. Do it only if there's a need.
    
    Thanks to DR0ID for his nice tiledtmxloader module:
        http://www.pygame.org/project-map+loader+for+%27tiled%27-1158-2951.html
    
    And the creators of Tiled Map Editor:
        http://www.mapeditor.org/
    """
    
    # Taken pretty much verbatim from the (old) tiledtmxloader module.
    #
    # The tiledtmxloader.TileMap object is stored in the returned
    # gamelib.Map object in attribute 'tiled_map'.
    
    world_map = TileMapParser().parse_decode_load(
        map_file_name, ImageLoaderPygame())
    tile_size = (world_map.tilewidth, world_map.tileheight)
    map_size = (world_map.width, world_map.height)
    gummworld_map = Map(tile_size, map_size)
    gummworld_map.tiled_map = world_map
    for layeri,layer in enumerate(world_map.layers):
        gummworld_map.layers.append(MapLayer(
            tile_size, map_size, layer.visible, True, True, name=str(layeri)))
        if not layer.visible and not load_invisible:
            continue
        for ypos in xrange(0, layer.height):
            for xpos in xrange(0, layer.width):
                x = (xpos + layer.x) * world_map.tilewidth
                y = (ypos + layer.y) * world_map.tileheight
                img_idx = layer.content2D[xpos][ypos]
                if img_idx == 0:
                    gummworld_map.add(None, layer=layeri)
                    continue
                try:
                    offx, offy, tile_img = world_map.indexed_tiles[img_idx]
                    screen_img = tile_img.copy()  #convert(tile_img)
                except KeyError:
                    print 'KeyError',img_idx,(xpos,ypos)
                    continue
                sprite = Sprite()
                ## Note: alpha conversion can actually kill performance.
                ## Do it only if there's a benefit.
                if convert_alpha:
                    if screen_img.get_alpha():
                        screen_img = screen_img.convert_alpha()
                    else:
                        screen_img = screen_img.convert()
                        if layer.opacity > -1:
                            screen_img.set_alpha(None)
                            alpha_value = int(255. * float(layer.opacity))
                            screen_img.set_alpha(alpha_value)
                            screen_img = screen_img.convert_alpha()
                sprite.image = screen_img
                sprite.rect = screen_img.get_rect(topleft=(x + offx, y + offy))
                sprite.name = xpos,ypos
                gummworld_map.add(sprite, layer=layeri)
    return gummworld_map

# load_tiled_tmx_map


def load_entities(filepath, cls_dict={}):
    """Load entities via the import_world_quadtree plugin. Return a list of
    entities.
    
    The cls_dict argument is a dict of classes to construct when encountering
    shape data. The following keys are supported: 'rect_cls', 'poly_cls',
    'circle_cls'. If any of those keys are missing from cls_dict, the following
    classes will be used by default: geometry.RectGeometry,
    geometry.PolyGeometry, geometry.CircleGeometry. Classes substituted in this
    manner must have constructors that are compatible with the default classes.
    """
#    import_script = data.filepath(
#        'plugins', os.path.join('map','import_world_quadtree.py'))
    State.world.remove(*State.world.entity_branch.keys())
    file_handle = open(filepath, 'rb')
#    locals_dict = {
#        'fh'         : file_handle,
#    }
#    locals_dict['rect_cls'] = cls_dict.get('rect_cls', RectGeometry)
#    locals_dict['poly_cls'] = cls_dict.get('poly_cls', PolyGeometry)
#    locals_dict['circle_cls'] = cls_dict.get('circle_cls', CircleGeometry)
#    execfile(import_script, {}, locals_dict)
    entities,tilesheets = import_world_quadtree(
        file_handle, RectGeometry, PolyGeometry, CircleGeometry)
    file_handle.close()
#    return locals_dict['entities']
    return entities,tilesheets

# load_world


def export_world_quadtree(fh, entities):
    """A quadtree-to-text exporter.
    
    This function is required by world_editor.py, and possibly other scripts, to
    export quadtree entities to a text file.
    
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
    
# export_world_quadtree


def import_world_quadtree(fh, rect_cls, poly_cls, circle_cls):
    """A world entity importer compatible with QuadTree.
    
    This function is required by world_editor.py, and possibly other scripts, to
    import world entities from a text file. It understands the format of files
    created by export_world_quadtree().

    Geometry classes used by this function to create shape objects are specified
    by the rect_cls, poly_cls, and circle_cls arguments. The constructor
    parameters must have the same signature as geometry.RectGeometry, et al.

    The values imported are those needed for each shape-class's constructor,
    plus a block of arbitrary user data which will be placed in the shape
    instance's user_data attribute.

    The user_data is also parsed for tilesheet info. Tilesets are loaded and
    returned as a dict of toolkit.Tilesheet, keyed by relative path to the
    image file.
    """
    
    if not issubclass(rect_cls, RectGeometry):
        raise pygame.error, 'argument "rect_cls" must be a subclass of geometry.RectGeometry'
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
    
# import_world_quadtree
    

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


def draw_sprite(s, blit_flags=0):
    """Draw a sprite on the camera's surface using world-to-screen conversion.
    """
    camera = State.camera
    cx,cy = camera.rect.topleft
    sx,sy = s.rect.topleft
    if haspygame19:
        camera.surface.blit(s.image, (sx-cx, sy-cy), special_flags=blit_flags)
    else:
        camera.surface.blit(s.image, (sx-cx, sy-cy))

# draw_sprite


def draw_tiles():
    """Draw visible tiles.
    
    This function assumes that the tiles stored in the map are sprites.
    """
    map = State.map
    layers = map.layers
    camera = State.camera
    visible_tile_range = camera.visible_tile_range
    blit = camera.surface.blit
    cx,cy = camera.rect.topleft
    realx,realy = camera._position
    for layeri in range(len(visible_tile_range)):
        layer = layers[layeri]
        if not layer.visible:
            continue
        left,top,right,bottom = visible_tile_range[layeri]
        mapw,maph = layer.map_size
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
                    blit(s.image, (rect.x-cx, rect.y-cy))

# draw_tiles


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


def draw_labels(layer=0):
    """Draw visible labels if enabled.
    
    Labels for the specified layer are blitted to the camera surface. If the
    layer has been collapsed with the collapse_map_layer() function so that
    the layer's tile size differs from the grid label sprites, this will look
    weird.
    """
    if State.show_labels:
        tile_range = State.camera.visible_tile_range
        if len(tile_range):
            x1,y1,x2,y2 = tile_range[layer]
            map_layer = State.map.layers[layer]
            get = map_layer.get_labels
            for s in get(x1,y1,x2,y2):
                draw_sprite(s)

# draw_labels


def draw_grid(layer=0):
    """Draw grid if enabled.
    
    Grids for the specified layer are blitted to the camera surface. If the layer
    has been collapsed with the collapse_map_layer() function so that the
    layer's tile size differs from the grid line sprites, this will look weird.
    """
    if State.show_grid:
        x1,y1,x2,y2 = State.camera.visible_tile_range[layer]
        # speed up access to grid lines and their rects
        map = State.map
        map_layer = map.layers[layer]
        tw,th = map_layer.tile_size
        vertical_grid_line = map_layer.vertical_grid_line
        horizontal_grid_line = map_layer.horizontal_grid_line
        map_rect = map.rect
        x1 = max(x1*tw, map_rect.left)
        x2 = min(x2*tw, map_rect.right)
        y1 = max(y1*th, map_rect.top)
        y2 = min(y2*th, map_rect.bottom)
        for y in xrange(y1,y2,th):
            for x in xrange(x1,x2,tw):
                pos = x,y
                draw_sprite(vertical_grid_line(pos))
                draw_sprite(horizontal_grid_line(pos))

# draw_grid
