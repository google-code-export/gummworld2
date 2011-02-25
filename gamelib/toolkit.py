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


from os.path import join as joinpath

import pygame
from pygame.locals import RLEACCEL
from pygame.sprite import Sprite

from gamelib import data, State, Map, MapLayer, Vec2d
from gamelib.geometry import RectGeometry, PolyGeometry, CircleGeometry
from gamelib.ui import HUD, Stat, Statf, hud_font
from tiledtmxloader import TileMapParser, ImageLoaderPygame


def make_hud(caption=None):
    """Create a HUD with dynamic items. This creates a default hud to serve
    both as an example, and for an early design and debugging convenience.
    """
    State.hud = HUD()
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


def collapse_map(map, num_tiles=(2,2)):
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
    for layeri,layer in enumerate(map.layers):
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
    # new map dimensions
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
    # walk the old map, stepping by the number of the tiles argument...
    for y in range(0, map.map_size.y, num_tiles.y):
        for x in range(0, map.map_size.x, num_tiles.x):
        # make a new sprite
            s = Sprite()
            s.image = pygame.surface.Surface((tw,th))
            s.rect = s.image.get_rect()
            s.name = tuple((x,y) / num_tiles)
            
            # blit (x,y) tile and neighboring tiles to right and lower...
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
#                new_layer[s.name] = s
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
    for s in base_layer:
        if s:
            news = pygame.sprite.Sprite()
            news.image = s.image.copy()
            news.rect = s.rect.copy()
            news.name = s.name
            s = news
        new_base_layer.append(s)
    # Blit the tiles in the specified layers.
    for layeri in layersi[1:]:
        layer = map.layers[layeri]
        if not layer.visible:
            # Skip invisible layers.
            continue
        for i,src_tile in enumerate(layer):
            if src_tile:
                x,y = src_tile.name
                s = new_base_layer.get_tile_at(x, y)
                if s is None:
                    s = pygame.sprite.Sprite()
                    s.name = x,y
                    s.image = src_tile.image.copy()
                    s.rect = src_tile.rect.copy()
                    new_base_layer[i] = s
                else:
                    s.image.blit(src_tile.image, (0,0))
    # Copy layers that were not specified and layers that are not invisible.
    for i,layer in enumerate(map.layers):
        if i in layersi and layer.visible:
            # Already been copied.
            continue
        new_layer = MapLayer(layer.tile_size, layer.map_size,
            visible=layer.visible, make_grid=True, make_labels=True,
            name=layer.name)
        new_map.insert(i, new_layer)
        for src_tile in layer:
            if src_tile:
                s = pygame.sprite.Sprite()
                s.name = src_tile.name
                s.image = src_tile.image.copy()
                s.rect = src_tile.rect.copy()
            else:
                s = None
            new_layer.append(s)
    
    return new_map

# reduce_map_layers


def load_tiled_tmx_map(map_file_name, load_invisible=False):
    """Load an orthogonal TMX map file that was created by the Tiled Map Editor.
    
    Thanks to dr0id for his nice tiledtmxloader module:
        http://www.pygame.org/project-map+loader+for+%27tiled%27-1158-2951.html

    And the creators of Tiled Map Editor:
        http://www.mapeditor.org/
    """
    
    # Taken pretty much verbatim from the tiledtmxloader module.
    #
    # The tiledtmxloader.TileMap object is stored in the returned
    # gamelib.Map object in attribute 'tiled_map'.
    
    world_map = TileMapParser().parse_decode_load(
        data.filepath('map', map_file_name), ImageLoaderPygame())
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
                    offx, offy, screen_img = world_map.indexed_tiles[img_idx]
                except KeyError:
                    print 'KeyError',img_idx,(xpos,ypos)
                    continue
                sprite = Sprite()
## Note: format conversion actually kills performance. ???
#                if screen_img.get_alpha():
#                    screen_img = screen_img.convert_alpha()
#                else:
#                    screen_img = screen_img.convert()
#                    if layer.opacity > -1:
#                        screen_img.set_alpha(None)
#                        alpha_value = int(255. * float(layer.opacity))
#                        screen_img.set_alpha(alpha_value)
#                        screen_img = screen_img.convert_alpha()
                sprite.image = screen_img  #.convert_alpha()
                sprite.rect = screen_img.get_rect(topleft=(x,y))
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
    import_script = data.filepath(
        'plugins', joinpath('map','import_world_quadtree.py'))
    State.world.remove(*State.world.entity_branch.keys())
    file_handle = open(filepath, 'rb')
    locals_dict = {
        'fh'         : file_handle,
    }
    locals_dict['rect_cls'] = cls_dict.get('rect_cls', RectGeometry)
    locals_dict['poly_cls'] = cls_dict.get('poly_cls', PolyGeometry)
    locals_dict['circle_cls'] = cls_dict.get('circle_cls', CircleGeometry)
    execfile(import_script, {}, locals_dict)
    file_handle.close()
    return locals_dict['entities']

# load_world


def draw_sprite(s, blit_flags=0):
    """Draw a sprite on the camera's surface using world-to-screen conversion.
    """
    camera = State.camera
    cx,cy = camera.rect.topleft
    sx,sy = s.rect.topleft
    camera.surface.blit(s.image, (sx-cx, sy-cy), special_flags=blit_flags)

# draw_sprite


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


def draw_labels(layer=0):
    """Draw visible labels if enabled.
    
    Labels for the specified layer are blitted to the camera surface. If the
    layer has been collapsed with the collapse_map_layer() function so that
    the layer's tile size differs from the grid label sprites, this will look
    weird.
    """
    if State.show_labels:
        x1,y1,x2,y2 = State.camera.visible_tile_range[layer]
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
        hline = map_layer.h_line
        vline = map_layer.v_line
        hrect = hline.rect
        vrect = vline.rect
        for s in map.get_tiles(x1, y1, x2, y2):
            srect = s.rect
            hrect.topleft = srect.bottomleft
            draw_sprite(hline)
            vrect.topleft = srect.topright
            draw_sprite(vline)

# draw_grid
