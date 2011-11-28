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


__doc__ = """supermap.py - Auto-loading / unloading multiple-maps grid for
Gummworld2.
"""
import pygame

from gummworld2 import State, Vec2d
from gummworld2.toolkit import get_visible_cell_ids, get_objects_in_cell_ids


NEIGHBORS = (N,NE,E,SE,S,SW,W,NW) = (
    (0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),
)
BORDERS = {
    N  : 'N',
    NE : 'NE',
    E  : 'E',
    SE : 'SE',
    S  : 'S',
    SW : 'SW',
    W  : 'W',
    NW : 'NW',
}


def print_supermap(super_map):
    """Print a supermap, its handlers, and each handler's triggers.
    """
    print super_map
    for from_name,map_handler in super_map.handlers.items():
        print '  %s' % map_handler
        for trigger in map_handler.triggers:
            border_name = trigger.border_name(from_name)
            print '    %s: %s' % (border_name, trigger)


def vadd(a,b):
    """Add 2D vectors a and b.
    """
    return (a[0]+b[0], a[1]+b[1])


def vsub(a,b):
    """Subtract 2D vector b from a.
    """
    return (a[0]-b[0], a[1]-b[1])


class _Trigger(object):
    """A collidable trigger in the map, used to trigger map loading.
    """
    
    def __init__(self, rect):
        """Construct a _Trigger object.
        
        rect is the bounding rect for the trigger, expressed in world space.
        """
        self.rect = pygame.Rect(rect)
        self.links = {}
        self.triggered = False
    
    def link(self, from_name, to_name):
        """Create a link.
        
        from_name is the map_handler.name that identifies the current map, i.e.
        super_map.current.name.
        
        to_name is the map_handler.name for the map that this trigger links to.
        """
        self.links[from_name] = to_name
    
    def __str__(self):
        return '<%s(%s, %s)>' % (
            self.__class__.__name__, self.rect, self.links,
        )
    

class MapHandler(object):
    """A MapHandler object is responsible for sensing when triggers have been
    tripped by a triggering rect (e.g. the camera), and loading and unloading
    its map.
    """
    
    def __init__(self, name, map_file):
        """Construct a MapHandler object.
        
        name is a tuple representing the 2D vector of this map in the SuperMap.
        The position in the SuperMap is relative to the origin map, so negative
        values are valid.
        
        map_file is a string containing the path to the map file used by the
        MapHandler.load() method.
        
        Attributes:
            
            name : The name argument from the constructor.
            
            map_file : The map_file argument from the constructor.
            
            rect : The bounding rect of this map in world space.
            
            supermap : The parent SuperMap object.
            
            map : The map object containing tiles. Current supported: BasicMap
            and TiledMap.
            
            triggers : The list of trigger objects linking this map to
            neighboring maps.
            
            timestamp : The time that this handler was last updated.
        """
        self.name = name
        self.map_file = map_file
        
        self.rect = None
        self.supermap = None
        self.map = None
        self.triggers = []
        
        # Last time _update() was called.
        self.timestamp = 0
    
    def _set_supermap(self, super_map):
        """Internal method called by SuperMap.add_handler() once it has received
        the origin map handler.
        """
        self.supermap = super_map
        
        # Set up my rect in world space.
        origin = super_map.origin
        if self.name == origin:
            self._load()
            self.rect = pygame.Rect(self.map.rect)
        elif not super_map.get_handler(origin):
            raise ValueError, 'must first add origin map to supermap'
        else:
            supermap_rect = super_map.get_handler(origin).rect
            self.rect = pygame.Rect(supermap_rect)
            w,h = self.rect.size
            offsetx,offsety = self.name
            x = self.rect.x + w * offsetx
            y = self.rect.y + h * offsety
            self.rect.topleft = x,y
        if __debug__: print '%s: rect %s' % (self.__class__.__name__, self.rect)
    
        # Set up triggers.
        name = self.name
        for border in NEIGHBORS:
            neighbor_name = vadd(name, border)
            neighbor = super_map.get_handler(neighbor_name)
            if neighbor:
                # share the trigger
                for t in neighbor.triggers:
                    if name == t.links.get(neighbor_name, None):
                        make_trigger(name, border, self.rect, t)
                        self.triggers.append(t)
                        if __debug__: print '%s: share trigger %s: %s' % (self.__class__.__name__, BORDERS[border], t)
            else:
                # make the trigger
                t = make_trigger(name, border, self.rect)
                self.triggers.append(t)
                if __debug__: print '%s: new trigger %s: %s' % (self.__class__.__name__, BORDERS[border], t)
    
    def get_objects(self, map_range):
        """Return a dict of tiles in the specified bounds.
        
        supermap_range is a dict of range specifications, such as returned by
        SuperMap.get_tile_range_in_rect().
        """
        return get_objects_in_cell_ids(self.map, map_range)
    
    def get_objects_in_rect(self, rect):
        """Return a dict of objects that intersect rect.
        
        rect is a pygame.Rect expressed in world coordinates.
        """
        map_range = self.get_tile_range_in_rect(rect)
        return get_objects_in_cell_ids(map_range)
    
    def get_tile_range_in_rect(self, rect):
        """Return a list of tile ranges, one for each layer, that intersect
        rect.
        
        rect is a pygame.Rect expressed in world coordinates.
        """
        if self.rect.colliderect(rect):
            r = pygame.Rect(rect)
            r.topleft = self.world_to_local(r.topleft)
            return get_visible_cell_ids(State.camera, self.map)
        else:
            return []
    
    def world_to_local(self, xy):
        """Convert a 2D vector in world space to a 2D vector in local space.
        
        This conversion is needed to translate maps, which use local space.
        """
        return Vec2d(xy) - self.rect.topleft
    
    def local_to_world(self, xy):
        """Convert a 2D vector in local space to a 2D vector in world space.
        
        This conversion is needed to translate maps, which use local space.
        """
#        return Vec2d(xy) + self.rect.topleft
        return vadd(xy, self.rect.topleft)
    
    def run_triggers(self, triggering_rect):
        """Run all triggers in this map versus the triggering_rect.
        
        The triggering rect is typically the camera rect. It is collision-
        checked against each trigger's rect to assess if neighboring map needs
        to be loaded.
        """
        triggered = False
        super_map = self.supermap
        current = super_map.current
        for trigger in self.triggers:
            if triggering_rect.colliderect(trigger.rect):
                trigger.triggered = True
                triggered = True
                other = trigger.links.get(current.name, None)
                if other:
                    map_handler = super_map.get_handler(other)
                    if map_handler:
                        map_handler._load()
            else:
                trigger.triggered = False
        return triggered
    
    def _load(self):
        """Internal load method.
        """
        if not self.map:
            if __debug__: print '%s: load map %s' % (self.__class__.__name__, self.name,)
            self.timestamp = State.clock._get_ticks()
            self.load()
    
    def _unload(self):
        """Internal unload method.
        """
        if self.map:
            if __debug__: print '%s: unload map %s' % (self.__class__.__name__, self.name,)
            self.unload()
            self.map = None
            if self.supermap.current == self.name:
                self.supermap.current = None
    
    def _update(self, dt):
        self.timestamp = State.clock._get_ticks()
        self.update(dt)
    
    def load(self):
        """Override this class. It must set self.map to a valid BasicMap or
        TiledMap object.
        
        This stub method does absolutely nothing to manage the map. To load the
        tile map, call the appropriate loader.
        
        Considerations:
            
            If a map is loaded (self.map is not None), this method will not be
            called.
            
            If a map was loaded, the unload method does not necessarily have to
            completely shut down a map. For example, Tiled maps can provide data
            for non-tile objects. Such object may have AI, or otherwise serve
            a purpose in the game logic. *IF* the tiles were unloaded but the
            objects were not, then you will need to extend this class to handle
            that situation since it will be desirable to reload the tiles on
            demand but undesirable to create more objects.
        """
        raise NotImplementedError()
    
    def unload(self):
        """Optional. Override this class to perform actions, such as saving the
        state of dynamic context, when the map is unloaded from memory.
        
        This stub method does absolutely nothing to manage the map. To unload
        the tile map, set self.map=None.
        """
        pass
    
    def enter(self):
        """Optional. Override this class to perform actions when the map is
        promoted to SuperMap.current.
        """
        pass
    
    def update(self, dt, *args):
        """Optional. Override this class to perform actions when the map is
        updated via SuperMap.update().
        """
        pass
    
    def exit(self):
        """Optional. Override this class to perform actions when the map is
        demoted from SuperMap.current.
        """
        pass
    
    def __str__(self):
        return '<%s(%s, %s)>' % (
            self.__class__.__name__, self.name, repr(self.map_file),
        )


class SuperMap(object):
    """
    SuperMap is a dict of MapHandler objects. The supermap is expressed in world
    coordinates. It uses map handlers to trigger map loading and unloading as
    the camera moves around the world.
    
    This class implements the required method signature for integration with the
    Camera class. Thus, State.map = SuperMap() is valid.
    
    Note that map tools in the toolkit module will not work with the SuperMap
    because those tools only know how to work with BasicMap or TiledMap objects
    where the map represents the entire world.
    
    The following SuperMap shows the names and relative positions of the maps
    in world space. The name is a tuple of int, length 2. In general it makes
    sense to have (0,0) be the origin map, but it is not required. A supermap
    can be irregular, and even have holes in it.
    
        +-------+-------+-------+
        |(-1,-1)| (0,-1)| (1,-1)|
        +-------+-------+-------+
        |(-1,0) | (0,0) | (1,0) |
        +-------+-------+-------+
        |(-1,1) | (0,1) | (1,1) |
        +-------+-------+-------+
    
    The following code adds three maps in single-row layout, starting with map
    (0,0) and proceeding to the right:
        
        class MyMapHandler(MapHandler):
            def load(self):
                self.map = load_a_map()
        supermap = SuperMap()
        supermap.add_handler(MyMapHandler((0,0), 'map00.tmx'))
        supermap.add_handler(MyMapHandler((1,0), 'map10.tmx'))
        supermap.add_handler(MyMapHandler((2,0), 'map20.tmx'))
    """
    
    def __init__(self, origin=(0,0), max_maps=4):
        """Construct a SuperMap object.
        
        origin is a tuple representing the 2D vector in the SuperMap which
        holds the SuperMap origin. The topleft of this maps rect will be set to
        (0,0) and all other maps' world space will be relative to this map.
        
        max_maps is an int representing the maximum number of maps to keep in
        memory. Maps above this number will be unloaded via the MapHandler
        based on the order in which they were last updated. The minimum
        functional value is 1. A value of 0 will never unload maps.
        
        Attributes:
            
            origin : origin from the constructor.
            
            max_maps : max_maps from the constructor.
            
            rect : The world bounding rect.
            
            handlers : A dict containing map handler objects, keyed by the tuple
            MapHandler.name.
            
            current : The current MapHandler object which contains the global
            camera's position (State.camera.position).
            
            visible_maps : The list of MapHandler objects that are visible
            within the global camera's rect (State.camera.rect).
            
            history : The list of loaded maps, ordered on last update.
        """
        self.origin = origin
        self.max_maps = max(0, max_maps)
        
        self.handlers = {}
        self.current = None
        self.visible_maps = []
        self.history = []
        
        self.rect = pygame.Rect(0,0,1,1)
    
    def set_current(self, map_handler):
        """Promote map_handler as the current map handler.
        
        map_handler is a MapHandler object to promote to current.
        
        If the current map handler is a valid MapHandler object, its exit()
        method will be called.
        
        Finally, map_handler's map will be loaded (as a failsafe; typically it
        is already loaded via a trigger), and its enter() method is called.
        """
        if __debug__: print '%s: current map %s -> %s' % (self.__class__.__name__, self.current, map_handler.name)
        if self.current:
            self.current.exit()
        self.current = map_handler
        if self.current:
            self.current._load()
            self.current.enter()
    
    def add_handler(self, map_handler):
        """Add map_handler to this SuperMap.
        
        map_handler is the MapHandler object to add to this SuperMap.
        """
        if __debug__: print '%s: add map %s' % (self.__class__.__name__, map_handler)
        if map_handler.name in self.handlers:
            raise KeyError, str(name) + ' key exists'
        # Add the map handler to this SuperMap.
        self.handlers[map_handler.name] = map_handler
        
        # Logic to initialize world space in each MapHandler.
        if self.current:
            # If origin already added, init world space for this MapHandler.
            map_handler._set_supermap(self)
            self.rect.unionall_ip([m.rect for m in self.handlers.values()])
        elif map_handler.name == self.origin:
            # This is the origin MapHandler. We can start intitializing world
            # space...
            self.set_current(map_handler)
            map_handler._set_supermap(self)
            # Init MapHandlers that were added prior to origin the MapHandler.
            for mh in self.handlers.values():
                if mh != map_handler:
                    mh._set_supermap(self)
            self.rect.unionall_ip([m.rect for m in self.handlers.values()])
        else:
            # Just a case to document that the origin MapHandler was not yet
            # added, so this MapHandler is simply squirreled away to be
            # initialized later in the case where origin MapHandler is added.
            pass
    
    def get_handler(self, name):
        """Return the named MapHandler object.
        
        name is a tuple representing the 2D vector of this map in this SuperMap.
        """
        return self.handlers.get(name, None)
    
    def get_objects(self, supermap_range):
        tiles_per_handler = {}
        for name,tile_range in supermap_range.items():
            map_handler = self.get_handler(name)
            if map_handler.map:
                tiles_per_handler[name] = map_handler.get_objects(tile_range)
        return tiles_per_handler
    
    def get_objects_in_rect(self, rect):
        tile_range = self.get_tile_range_in_rect(rect)
        return self.get_objects(tile_range)
    
    def get_tile_range_in_rect(self, rect):
        """rect must be in world space.
        """
        range_per_handler = {}
        for map_handler in self.visible_maps:
            range_per_handler[map_handler.name] = map_handler.get_tile_range_in_rect(rect)
        return range_per_handler
    
    def update(self, dt, *args):
        """Update this SuperMap.
        
        This method runs each MapHandler's triggers, promotes a MapHandler to
        current when appropriate, and calls each MapHandler's update() method.
        """
        history = self.history
        visible_maps = self.visible_maps
        del visible_maps[:]
        cam_rect = State.camera.rect
        colliderect = cam_rect.colliderect
        current = self.current
        
        # Update current. Run triggers.
        current._update(dt)
        current.run_triggers(cam_rect)
        visible_maps.append(current)
        if current not in history:
            history.append(current)
        
        # Update visible map handlers. Switch current if appropriate.
        current_name = current.name
        for neighbor in NEIGHBORS:
            map_handler = self.get_handler(vadd(neighbor, current_name))
            if map_handler:
                map_handler_rect = map_handler.rect
                if map_handler_rect.colliderect(cam_rect):
                    map_handler.update(dt)
                    visible_maps.append(map_handler)
                    if map_handler not in history:
                        history.append(map_handler)
                if map_handler_rect.collidepoint(cam_rect.center):
                    self.set_current(map_handler)
        visible_maps.sort(key=map_handler_name)
        
        # Check history, unload stale maps.
        max_maps = self.max_maps
        history.sort(key=map_handler_timestamp)
        if max_maps:
            for map_handler in history[:-max_maps]:
                if map_handler not in visible_maps:
                    history.remove(map_handler)
                    map_handler._unload()
        
        self.visible_objects = self.get_objects_in_rect(State.camera.rect)
    
    def draw(self):
        camera = State.camera
        camera_rect = camera.rect
        blit = camera.surface.blit
        cx,cy = camera_rect.topleft
        get_handler = self.get_handler
        for name,layers in self.visible_objects.items():
            if not layers:
                continue
            local_to_world = get_handler(name).local_to_world
            for sprites in layers:
                for sprite in sprites:
                    sx,sy = local_to_world(sprite.rect.topleft)
                    pos = sx-cx, sy-cy
                    blit(sprite.image, pos)

def map_handler_name(map_handler):
    x,y = map_handler.name
    return y,x


def map_handler_timestamp(map_handler):
    return map_handler.timestamp


def make_trigger(name, border, rect, trigger=None):
    #print 'make_trigger',name, border, rect, trigger
    attrs = {
        N : 'top',
        S : 'bottom',
        E : 'right',
        W : 'left',
        NE : 'topright',
        SE : 'bottomright',
        SW : 'bottomleft',
        NW : 'topleft',
    }
    if border in (NE,SE,SW,NW):
        r = pygame.Rect(0,0,200,200)
        r.center = getattr(rect,attrs[border])
    elif border in (N,S):
        r = pygame.Rect(0,0,rect.w,100)
        r.center = rect.centerx, getattr(rect,attrs[border])
    elif border in (E,W):
        r = pygame.Rect(0,0,100,rect.h)
        r.center = getattr(rect,attrs[border]), rect.centery
    if not trigger:
        trigger = _Trigger(r)
    # Set up linkage. e.g. if map name is 1,0 and border is E (1,0), then
    # trigger.links[1,0]=2,0
    neighbor = vadd(name, border)
    trigger.link(name, neighbor)
    return trigger
