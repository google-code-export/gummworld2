import pygame

from tiledtmxloader.tiledtmxloader import TileMap, TileMapParser
from tiledtmxloader.helperspygame import ResourceLoaderPygame, RendererPygame


def sortkey_x(tile):
    return tile.rect.x


def sortkey_y(tile):
    return tile.rect.y


class TiledMap(TileMap):
    
    def __init__(self, tmx_file, collapse_level=1, sortkey=None):
        """Construct a TiledMap object.
        
        This is a map based closely on tiledtmxloader.TileMap. It exposes the
        basic features of the TileMap and RendererPygame classes. It has a
        TileMap and RendererPygame object in public attributes for complete
        access to the objects.
        
        tmx_file is the path and filename of the TMX map file.
        
        collapse_level is the starting collapse level of all the layers. Note
        that if you don't want every layer collapsed, or different collapse
        levels per layer, leave this at the default of 1 and pick individual
        tile layers to collapse (TiledMap.get_tile_layer()).
        
        sortkey is the function to pass to sort(key=func) when a
        TiledMap.get_tiles() or TiledMap.get_tiles_in_rect() is called. The
        default value of None results in an unsorted layer. A couple common
        functions are provided in the module: sortkey_x() sortkey_y().
        """
        map = TileMapParser().parse_decode(tmx_file)
        resources = ResourceLoaderPygame()
        resources.load(map)
        self.tiled_map = map
        self.renderer = RendererPygame(resources, collapse_level)
        
        self.sortkey = sortkey
        
        tw,th = map.tilewidth, map.tileheight
        mw,mh = map.width, map.height
        self.rect = pygame.Rect(0,0,tw*mw,th*mh)
    
    @property
    def width(self):
        return self.tiled_map.width
    @property
    def height(self):
        return self.tiled_map.width
    @property
    def size(self):
        return self.width,self.height
    @property
    def tile_width(self):
        return self.tiled_map.tilewidth
    @property
    def tile_height(self):
        return self.tiled_map.tileheight
    @property
    def tile_size(self):
        return self.tile_width,self.tile_height
    @property
    def pixel_width(self):
        return self.tiled_map.pixel_width
    @property
    def pixel_height(self):
        return self.tiled_map.pixel_height
    
    def get_layer(self, layeri):
        """Return the layer indexed by layeri.
        
        This method can return a tile layer or an object layer. The layer type
        can be detected via the attribute layer.is_object_group.
        """
        idx = self.tiled_map.layers[layeri]
        return self.renderer._layers[idx]
    
    def get_tile_layer(self, layeri):
        """Return the tile layer indexed by layeri.
        """
        return self.get_tile_layers()[layeri]
    
    def get_tile_layers(self):
        rl = self.renderer._layers
        return [rl[i] for i in self.tiled_map.layers if not i.is_object_group]
    
    def get_object_group(self, groupi):
        return self.get_object_groups()[groupi]
    
    def get_object_groups(self):
        return [i for i in self.tiled_map.layers if i.is_object_group]
    
    def get_tile_at(self, x, y, layeri=0):
        layer = self.get_layer(layeri)
        return layer.content2D[x][y]
    
    def rect_to_range(self, rect, layeri=0):
        layer = self.get_layer(layeri)
        tw,th = layer.tilewidth, layer.tileheight
        x1,y1,w,h = rect
        x2 = (x1+w) / tw + 1
        y2 = (y1+h) / th + 1
        x1 = x1 / tw - 1
        y1 = y1 / th - 1
        if x1 < 0: x1 = 0
        if y1 < 0: y1 = 0
        if x2 < 0: x2 = 0
        if y2 < 0: y2 = 0
        return x1,y1,x2,y2
    
    def get_tiles_in_rect(self, rect, layeri=0):
        tiles = []
        content2D = self.get_layer(layeri).content2D
        x1,y1,x2,y2 = self.rect_to_range(rect, layeri)
        for column in content2D[x1:x2+1]:
            tiles.extend([t for t in column[y1:y2+1] if t])
        if self.sortkey:
            tiles.sort(key=self.sortkey)
        return tiles
    
    def get_tile_range_in_rect(self, rect):
        tile_ranges = []
        for layeri in range(len(self.tiled_map.layers)):
            layer = self.get_layer(layeri)
            tile_w = layer.tilewidth
            tile_h = layer.tileheight
            l,t,w,h = rect
            r = l+w-1
            b = t+h-1
            left = int(round(float(l) / tile_w)) - 1
            right = int(round(float(r) / tile_w)) + 1
            top = int(round(float(t) / tile_h)) - 1
            bottom = int(round(float(b) / tile_h)) + 1
            tile_ranges.append((left,top,right,bottom))
        return tile_ranges
    
    def get_tiles(self, tile_range):
        tiles_per_layer = []
        if tile_range:
            for layeri,layer in enumerate(self.get_tile_layers()):
                layer_range = tile_range[layeri]
                if layer_range and layer.visible:
                    mapw = layer.num_tiles_x
                    maph = layer.num_tiles_y
                    x1,y1,x2,y2 = layer_range
                    if x1 < 0: x1 = 0
                    if y1 < 0: y1 = 0
                    if x2 > mapw: x2 = mapw
                    if y2 > maph: y2 = maph
                    c2d = layer.content2D
                    tiles = [t for t in
                        [c2d[x][y] for y in range(y1,y2) for x in range(x1,x2)]
                        if t
                    ]
                    if self.sortkey:
                        tiles.sort(key=self.sortkey)
                tiles_per_layer.append(tiles)
        return tiles_per_layer
    
    def get_objects(self, group_name=None):
        objects = []
        if group_name:
            objects.extend(self.tiled_map.object_groups[group_name])
        else:
            for group in self.tiled_map.object_groups.items():
                objects.extend(group)
        return objects
    
    def collapse(self, collapse_level, layeri=None):
        if layeri is None:
            layers = self.get_tile_layers()
        else:
            layers = [self.get_layer(layeri)]
        for layer in layers:
            layer.collapse(collapse_level)
