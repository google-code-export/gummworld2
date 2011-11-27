import pygame

from tiledtmxloader.helperspygame import get_layers_from_map, SpriteLayer
from tiledtmxloader.tiledtmxloader import TileMap, TileMapParser
from tiledtmxloader.helperspygame import ResourceLoaderPygame, RendererPygame

from gummworld2 import BasicMap, BasicLayer
from gummworld2 import spatialhash


class TiledMap(BasicMap):
    
    def __init__(self, map_file_name, collapse=(1,1), collapse_layers=None, load_invisible=True):
        """Construct a TiledMap object.
        
        the map_file_name argument is the path and filename of the TMX map file.
        
        The collapse argument is the number of tiles on the X and Y axes to
        join.
        
        The collapse_layers argument is a sequence of indices indicating to
        which TiledMap.layers the collapse algorithm should be applied. See the
        tiledmap.collapse_map.
        
        If you don't want every layer collapsed, or different collapse values
        per layer, use the default of (1,1) and pick individual tile layers to
        collapse via TileMap.collapse(), collapse_map(), or collapse_layer().
        """
        self.layers = []
        self.raw_map = _load_tiled_tmx_map(map_file_name, self, load_invisible)
        
        tmp_layers = self.layers
        
        BasicMap.__init__(self,
            self.raw_map.width, self.raw_map.height,
            self.raw_map.tilewidth, self.raw_map.tileheight)
        
        self.layers = tmp_layers
        
        self.orientation = self.raw_map.orientation
        self.properties = self.raw_map.properties
        self.map_file_name = self.raw_map.map_file_name
        self.named_layers = self.raw_map.named_layers
        
        if collapse > (1,1):
            collapse_map(self, collapse, collapse_layers)
    
    def get_layer_by_name(self, layer_name):
        return self.named_layers[layer_name]
    
    def get_tile_layers(self):
        rl = self.layers
        return [L for L in self.layers if not L.is_object_group]
    
    def get_object_groups(self):
        return [L for L in self.layers if L.is_object_group]


class TiledLayer(object):
    
    def __init__(self, parent_map, layer, layeri):
        self.parent_map = parent_map
        
        # layer may be an instance of TiledLayer or tiledtmxloader.TileLayer
        if isinstance(layer, TiledLayer):
            tile_width = layer.tile_width
            tile_height = layer.tile_height
        else:
            tile_width = layer.tilewidth
            tile_height = layer.tileheight
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.width = layer.width
        self.height = layer.height
        self.pixel_width = self.width * tile_width
        self.pixel_height = self.height * tile_height
        
        cell_size = max(tile_width, tile_height)
        self.rect = pygame.Rect(0,0, layer.pixel_width+1, layer.pixel_height+1)
        self.objects = spatialhash.SpatialHash(self.rect, cell_size)
        
        self.layeri = layeri
        
        self.name = layer.name
        self.properties = layer.properties
        self.opacity = layer.opacity
        self.visible = layer.visible
        self.is_object_group = layer.is_object_group
    
    def add(self, tile):
        self.objects.add(tile)
    
    def get_tiles_in_rect(self, rect):
        return self.objects.intersect_rect(rect)


def _load_tiled_tmx_map(map_file_name, gummworld_map, load_invisible=True):
    """Load an orthogonal TMX map file that was created by the Tiled Map Editor.
    
    If load_invisible is False, layers where visible!=0 will be empty. Their
    tiles will not be loaded.
    
    Thanks to DR0ID for his nice tiledtmxloader module:
        http://www.pygame.org/project-map+loader+for+%27tiled%27-1158-2951.html
    
    And the creators of Tiled Map Editor:
        http://www.mapeditor.org/
    """
    
    # Taken pretty much verbatim from the (old) tiledtmxloader module.
    #
    # The tiledtmxloader.TileMap object is stored in the returned
    # gamelib.Map object in attribute 'tiled_map'.
    
    from pygame.sprite import Sprite
    
    world_map = TileMapParser().parse_decode(map_file_name)
    resource = ResourceLoaderPygame()
    resource.load(world_map)
    tile_size = (world_map.tilewidth, world_map.tileheight)
    map_size = (world_map.width, world_map.height)
    
    for layeri,layer in enumerate(world_map.layers):
        gummworld_layer = TiledLayer(gummworld_map, layer, layeri)
        gummworld_map.layers.append(gummworld_layer)
        if not layer.visible and not load_invisible:
            continue
        for ypos in xrange(0, layer.height):
            for xpos in xrange(0, layer.width):
                x = (xpos + layer.x) * layer.tilewidth
                y = (ypos + layer.y) * layer.tileheight
                img_idx = layer.content2D[xpos][ypos]
                if img_idx == 0:
                    continue
                try:
                    offx,offy,tile_img = resource.indexed_tiles[img_idx]
                    screen_img = tile_img
                except KeyError:
                    print 'KeyError',img_idx,(xpos,ypos)
                    continue
                sprite = Sprite()
                ## Note: alpha conversion can actually kill performance.
                ## Do it only if there's a benefit.
#                if convert_alpha:
#                    if screen_img.get_alpha():
#                        screen_img = screen_img.convert_alpha()
#                    else:
#                        screen_img = screen_img.convert()
#                        if layer.opacity > -1:
#                            screen_img.set_alpha(None)
#                            alpha_value = int(255. * float(layer.opacity))
#                            screen_img.set_alpha(alpha_value)
#                            screen_img = screen_img.convert_alpha()
                sprite.image = screen_img
                sprite.rect = screen_img.get_rect(topleft=(x + offx, y + offy))
                sprite.name = xpos,ypos
                gummworld_layer.add(sprite)
    return world_map


def collapse_map(map_, num_tiles=(2,2), which_layers=None):
    """Collapse which_layers in map_ by joining num_tiles into one tile.
    
    The map_ argument is the map to manipulate. It must be an instance of
    TiledMap.
    
    The num_tiles argument is a tuple representing the number of tiles in the X
    and Y axes to combine.
    
    which_layers is the list of indicides for the map_.layers list that
    will be collapsed.
    
    If a map area is sparse (fewer tiles than num_tiles[0] * num_tiles[1]) the
    tiles will be kept as they are.
    
    If tiles with different characteristics are joined, the results can be
    unexpected. These characteristics include some flags, depth, colorkey. This
    can be avoided by pre-processing the map to convert all images so they have
    compatible characteristics.
    """
    from gummworld2 import Vec2d
    
    # new map dimensions
    num_tiles = Vec2d(num_tiles)
    tw,th = (map_.tile_width,map_.tile_height) * num_tiles
    mw,mh = (map_.width,map_.height) // num_tiles
    if mw * num_tiles.x != map_.pixel_width:
        mw += 1
    if mh * num_tiles.y != map_.pixel_height:
        mh += 1
    map_.tile_width = tw
    map_.tile_height = th
    map_.width = mw
    map_.height = mh
    # collapse the tiles in each layer...
    if which_layers is None:
        which_layers = range(len(map_.layers))
    for layeri in which_layers:
        layer = map_.layers[layeri]
        if layer.is_object_group:
            continue
        new_layer = TiledLayer(map_, layer, layeri)
        collapse_layer(layer, new_layer, num_tiles)
        print len(layer.objects),len(new_layer.objects)
        # add a new layer
        map_.layers[layeri] = new_layer


def collapse_layer(old_layer, new_layer, num_tiles=(2,2)):
    """Collapse a single layer by joining num_tiles into one tile. A new layer
    is returned.
    
    The old_layer argument is the layer to process.
    
    The new_layer argument is the layer to build.
    
    The num_tiles argument is a tuple representing the number of tiles in the X
    and Y axes to join.
    
    If a map area is sparse (fewer tiles than num_tiles[0] * num_tiles[1]) the
    tiles will be kept as they are.
    
    If tiles with different characteristics are joined, the results can be
    unexpected. These characteristics include some flags, depth, colorkey. This
    can be avoided by pre-processing the map to convert all images so they have
    compatible characteristics.
    """
    from pygame.sprite import Sprite
    from gummworld2 import Vec2d
    
    # New layer dimensions.
    num_tiles = Vec2d(num_tiles)
    tw,th = (old_layer.tile_width,old_layer.tile_height) * num_tiles
    mw,mh = (old_layer.width,old_layer.height) // num_tiles
    if mw * num_tiles.x != old_layer.pixel_width:
        mw += 1
    if mh * num_tiles.y != old_layer.pixel_height:
        mh += 1
    # Poke the right values into new_layer.
    cell_size = max(tw,th) * 2
    new_layer.objects = spatialhash.SpatialHash(old_layer.rect, cell_size)
    new_layer.width = mw
    new_layer.height = mh
    new_layer.tile_width = tw
    new_layer.tile_height = th
    # Grab groups of map sprites, joining them into a single larger image.
    query_rect = pygame.Rect(0,0,tw-1,th-1)
    for y in range(0, mh*th, th):
        for x in range(0, mw*tw, tw):
            query_rect.topleft = x,y
##            print '----\n',query_rect
            sprites = old_layer.objects.intersect_objects(query_rect)
##            print [s.rect.topleft for s in sprites]
            if len(sprites) != num_tiles.x * num_tiles.y:
##                print 'not enough sprites:',len(sprites)
                continue
            # If sprite images have different characteristics, they cannot be
            # reliably collapsed. In which case, keep them as-is.
            incompatible = False
            image = sprites[0].image
            flags = image.get_flags() ^ pygame.SRCALPHA
            colorkey = image.get_colorkey()
            depth = image.get_bitsize()
# This is probably too restrictive. However, some combinations of tiles may
# give funky results.
#            all_details = (flags,colorkey,depth)
#            for s in sprites[1:]:
#                if all_details != (
#                        s.image.get_flags(),
#                        s.image.get_colorkey(),
#                        s.image.get_bitsize(),
#                ):
#                    incompatible = True
#            if incompatible:
#                print 'collapse_layer: incompatible image characteristics'
#                for s in sprites:
#                    new_layer.add(s)
#                continue
            # Make a new sprite.
            new_sprite = Sprite()
            new_sprite.rect = sprites[0].rect.unionall([s.rect for s in sprites[1:]])
            new_sprite.rect.topleft = x,y
            new_sprite.image = pygame.surface.Surface(new_sprite.rect.size, flags, depth)
            if colorkey:
                new_sprite.image.set_colorkey(colorkey)
            
            # Blit (x,y) tile and neighboring tiles to right and lower...
            left = reduce(min, [s.rect.x for s in sprites])
            top = reduce(min, [s.rect.y for s in sprites])
            for sprite in sprites:
                p = sprite.rect.x - left, sprite.rect.y - top
##                print sprite.rect.topleft,p
                new_sprite.image.blit(sprite.image.convert(depth, flags), p)
            new_layer.add(new_sprite)
    return new_layer
