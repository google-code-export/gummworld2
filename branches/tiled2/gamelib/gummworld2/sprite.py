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


__doc__ = """sprite.py - Camera target sprite, free-roaming bucket sprite, and
a bucket sprite group.
"""


import pygame

from gummworld2 import toolkit, State, Vec2d


class CameraTargetSprite(pygame.sprite.Sprite):
    """A sample camera target sprite, a la pygame.sprite.Sprite.
    
    An instance of this class is intended to be the Camera.target for games that
    want to use a sprite for the Camera target. It differs from other sprites in
    that its screen position is stationary even though it moves around the
    game's map.
    
    A position property is required. It is highly recommended the points be a
    Vec2d(float,float). Setting position should also set Sprite.rect.center,
    which should be rounded. Sprite.rect.center can be used in collision tests
    versus other sprites or rects expressed in terms of world coordinates.
    
    This sprite should typically be blitted using the value in screen_position.
    It is never changed, so it will always be drawn in the same location on the
    screen.
    """
    
    def __init__(self):
        super(CameraTargetSprite, self).__init__()
        self._position = Vec2d(0.0,0.0)
        self._screen_position = Vec2d(0.0,0.0)
    
    @property
    def position(self):
        """Map position in float coordinates.
        
        For rounded integer (pixel) position read the rect attributes.
        
        The property setter updates rect.center. If a different rect attribute
        is desired, subclass CameraTargetSprite and override the setter.
        """
        return self._position
    @position.setter
    def position(self, val):
        p = self._position
        p.x,p.y = float(val[0]),float(val[1])
        self.rect.center = int(round(p.x)), int(round(p.y))
    
    @property
    def screen_position(self):
        """Screen position in int coordinates.
        """
        return self._screen_position - Vec2d(self.rect.size) // 2
    @screen_position.setter
    def screen_position(self, val):
        x,y = val
        pos = self._screen_position
        pos.x,pos.y = int(round(x)), int(round(y))


class BucketSprite(pygame.sprite.Sprite):
    """A sample sprite, a la pygame.sprite.Sprite.
    
    This class is for sprites that move around the world and are displayed
    independently of the camera.
    
    A position property is required. It is highly recommended the points be a
    Vec2d(float,float). Setting position should also set Sprite.rect.center,
    which should be rounded.
    
    All sprite positions must be in world coordinates. This means they cannot be
    blitted straight to the screen using methods like pygame.sprite.Group.
    (pygame's Group blits using the rect, which is not expressed in screen
    coordinates in Gummworld2.) Instead use something like the draw() function
    provided here, or better yet a batch draw routine to minimize repetitive
    attribute access, such as that in BucketGroup.
    
    A final consideration for sprites is the sprite group. If the sprite uses a
    pygame group, then no special consideration need be given other than to
    use a custom draw() method. However, this Sprite is designed expressly for
    the BucketGroup class. Whenever the sprite moves, it checks what bucket it's
    in and hops to another bucket if it should. This is required so the
    BucketGroup's sprites_in_range() and buckets_in_range() methods work
    properly and retrieve sprites efficiently.
    """

    def __init__(self, position=(0,0)):
        """Construct an instance of BucketSprite.
        
        One may subclass BucketSprite or simply set its members (image, rect,
        etc.) as with pygame sprites. If setting a rect, be sure to update its
        position property afterwards:
            
            s = BucketSprite()
            s.image = ...
            s.rect = s.image.get_rect()
            s.position = s.position  ## or some other value within map bounds
        """
        super(BucketSprite, self).__init__()
        self._position = Vec2d(0.0,0.0)
    
    @property
    def position(self):
        """Map position in float coordinates.
        
        For rounded integer (pixel) position read the rect attributes.
        
        The property setter updates rect.center. If a different rect attribute
        is desired, Subclass BucketSprite and override the setter.
        """
        return self._position
    @position.setter
    def position(self, val):
        p = self._position
        p.x,p.y = float(val[0]),float(val[1])
        self.rect.center = int(round(p.x)), int(round(p.y))
        if hasattr(self, 'bucket'):
            self._move_bucket()

    def _move_bucket(self):
        mapx,mapy = self.position / State.map.tile_size
        mapx,mapy = int(round(mapx)), int(round(mapy))
        if self.bucket != (mapx,mapy):
            bucket = self.bucket_group.buckets[self.bucket]
            del bucket[self]
            bucket = self.bucket_group.buckets[mapx,mapy]
            bucket[self] = 1
            self.bucket = (mapx,mapy)
    
    
    def draw(s, blit_flags=0):
        """Draw a sprite on the camera's surface using world-to-screen conversion.
        """
        camera = State.camera
        cx,cy = camera.rect.topleft
        sx,sy = s.rect.topleft
        camera.surface.blit(s.image, (sx-cx, sy-cy), special_flags=blit_flags)


class BucketGroup(pygame.sprite.Group):
    """A sprite group that provides buckets.
    
    The buckets correlate to the map tile grid. Tile 0,0 is bucket 0,0, tile 8,9
    is bucket 8,9, and so on.
    
    Instances of this class get, update, and draw sprites in 2D ranges of
    buckets. The sprites are responsible for hopping from bucket to bucket as
    needed, whenever they move. (If you use the BucketSprite this behavior is
    built in.)
    """
    
    def __init__(self, tile_size, map_size, *sprites):
        """Construct an instance of BucketGroup.
        """
        super(BucketGroup, self).__init__()
        self.tile_size = Vec2d(tile_size)
        self.map_size = Vec2d(map_size)
        x1,y1 = 0,0
        x2,y2 = map_size
        self.buckets = dict()
        self.buckets.update([ ((x,y), {})
            for x in range(x1,x2+1)
                for y in range(y1,y2+1)
        ])
        self.add(*sprites)
    
    def copy(self):
        ## This certainly won't work. The BucketSprite only tracks one bucket
        ## group, and copying them would clobber it. BucketSprite.bucket_group
        ## needs to be implemented as a container before multiple group
        ## membership would work.
#        """Return a copy of the bucket group.
#        """
#        new_group = self.__class__(self.tile_size, self.map_size, *self.sprites())
#        return new_group
        return None
    
    def add(self, *sprites):
        if len(sprites):
            super(BucketGroup, self).add(*sprites)
            tw,th = self.tile_size
            for s in sprites:
                tx,ty = s.rect.center
                mx,my = tx//tw, ty//th
                bucket = self.buckets[mx,my]
                bucket[s] = 1
                s.bucket_group = self
                s.bucket = (mx,my)
    
    def remove_internal(self, sprite):
        try:
            bucket = self.buckets[sprite.bucket]
            del bucket[sprite]
        except:
            pass
        super(BucketGroup, self).remove_internal(sprite)
    
    def update(self, dim=None, *args):
        if dim is None:
            sprites = self.sprites()
        else:
            sprites = []
            for bucket in self.buckets_in_range(dim):
                sprites.extend(bucket.keys())
        for s in sprites:
            s.update(*args)
    
    def draw(self, dim=None):
        blit = toolkit.draw_sprite
        if dim is None:
            for bucket in self.sprites():
                for s in bucket:
                    blit(s)
        else:
            for bucket in self.buckets_in_range(dim):
                for s in bucket:
                    blit(s)
        del self.lostsprites[:]
    
    def sprites_in_range(self, dim=None):
        """Return a list of sprites in the range specified by dim.
        
        The optional dim argument is a tuple(x1,y1,x2,y2) range of grid
        coordinates. If dim is None, all sprites are returned.
        """
        if dim is None:
            dim = 0,0,self.map_size.x+1,self.map_size.y+1
        sprites = []
        for bucket in self.buckets_in_range(dim):
            sprites.extend(bucket.keys())
        return sprites
    
    def buckets_in_range(self, dim=None):
        """Return a list of buckets in the range specified by dim.
        
        The optional dim argument is a tuple(x1,y1,x2,y2) range of grid
        coordinates. If dim is None, all buckets are returned.
        """
        if dim is None:
            dim = 0,0,self.map_size.x+1,self.map_size.y+1
        buckets = self.buckets
        x1,y1,x2,y2 = dim
        get = buckets.get
        return [
            d for d in (get((x,y), {})
                for x in range(x1,x2)
                    for y in range(y1,y2)
            ) if d
        ]
    
    def empty(self):
        super(BucketGroup, self).empty()
        for bucket in self.buckets:
            bucket.clear()
