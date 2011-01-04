import pygame

from gamelib import toolkit, State, Vec2d

class BucketSprite(pygame.sprite.Sprite):
    """A sample sprite, a la pygame.
    
    A position property is required. It is highly recommended the points be a
    Vec2d(float,float). Setting position should also set Sprite.rect.center,
    which should be rounded.
    
    All sprite positions must be in world coordinates. This means they cannot be
    blitted straight to the screen using methods like pygame.sprite.Group.
    pygame's Group blits using the rect, which is not expressed in screen
    coordinates. Instead use something like the draw() function provided here,
    or better yet a batch draw routine to minimize repetitive attribute access.
    
    A final consideration for sprites is the sprite group. If the sprite uses a
    pygame group, then no special consideration need be given other than to
    avoid using its draw() method. This Sprite is designed for the BucketGroup
    class. Whenever the sprite moves, it checks what bucket it's in and hops to
    another bucket if it should. This is required so the BucketGroup's
    sprites_in_range() and buckets_in_range() methods work properly.
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
        """Float position in map coordinates.
        
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
    
    def __init__(self, map, *sprites):
        """Construct an instance of BucketGroup.
        """
        super(BucketGroup, self).__init__()
        self.map = map
        x1,y1 = 0,0
        x2,y2 = map.map_size
        self.buckets = dict()
        self.buckets.update([ ((x,y), {})
            for x in range(x1,x2+1)
                for y in range(y1,y2+1)
        ])
        self.add(*sprites)
    
### TO DO ###
#    def copy(self):
#        pass
    
    def add(self, *sprites):
        if len(sprites):
            super(BucketGroup, self).add(*sprites)
            tw,th = self.map.tile_size
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
    
    def update(self, dim, *args):
        for bucket in self.buckets_in_range(dim):
            for s in bucket.keys():
                s.update(*args)
    
    def draw(self, dim):
        blit = toolkit.draw_sprite
        for bucket in self.buckets_in_range(dim):
            for s in bucket:
                blit(s)
        del self.lostsprites[:]
    
    def sprites_in_range(self, dim):
        sprites = []
        for bucket in self.buckets_in_range(dim):
            sprites.extend(bucket.keys())
        return sprites
    
    def buckets_in_range(self, dim):
        buckets = self.buckets
        x1,y1,x2,y2 = dim
        get = buckets.get
        return [
            d for d in (get((x,y), {})
                for x in range(x1,x2)
                    for y in range(y1,y2)
            ) if d
        ]
    
### TO DO ###
#    def clear_in_range(self, surface, dim):
#        pass
    
    def empty(self):
        super(BucketGroup, self).empty()
        for bucket in self.buckets:
            bucket.clear()
