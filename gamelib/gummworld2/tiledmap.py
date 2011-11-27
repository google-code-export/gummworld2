import pygame

from tiledtmxloader.helperspygame import get_layers_from_map, SpriteLayer
from tiledtmxloader.tiledtmxloader import TileMap, TileMapParser
from tiledtmxloader.helperspygame import ResourceLoaderPygame, RendererPygame

from gummworld2 import spatialhash
from gummworld2.basicmap import BasicMap, BasicLayer, collapse_layer


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
#            collapse_map(self, collapse, collapse_layers)
            self.collapse(collapse, collapse_layers)
    
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
    
    def __len__(self):
        return len(self.objects.cell_ids)
    
    def collapse(self, collapse=(1,1)):
        if collapse <= (1,1):
            return
        new_layer = TiledLayer(self.parent_map, self, self.layeri)
        collapse_layer(self, new_layer, collapse)
        self.parent_map.layers[self.layeri] = new_layer


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
