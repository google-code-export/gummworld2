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


__doc__ = """23_supermap.py - An example of using SuperMap in Gummworld2.
"""


import cProfile, pstats

import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import Engine, State, View, SuperMap, MapHandler, TiledMap, Statf
from gummworld2 import context, data, toolkit, model, supermap


COLLAPSE_KEYS = range(K_1, K_9+1)


class App(Engine):
    
    def __init__(self):
        resolution = 320,240
#        resolution = 640,480
#        resolution = 800,600
        self.movex = 0
        self.movey = 0
        self.visible_tiles = {}
        
        # Init Engine, no map or world.
        Engine.__init__(self,
            resolution=resolution, #display_flags=DOUBLEBUF,
            camera_target=model.Object(),
            frame_speed=0,
        )
        # Create the supermap and world.
        make_supermap(self)
        self.camera.init_position(self.map.current.rect.center)
        
        # Show me da goods.
        toolkit.make_hud()
        State.hud.add('Current', Statf(State.hud.next_pos(),
            'Current Map %s', callback=lambda:'%s'%str(State.map.current.name), interval=.5))
        State.hud.add('Visible', Statf(State.hud.next_pos(),
            'Visible %s', callback=lambda:str(len(State.map.visible_maps)), interval=.5))
        State.hud.add('History', Statf(State.hud.next_pos(),
            'History %s', callback=lambda:'%s/%s'%(str(len(State.map.history)),str(State.map.max_maps)), interval=.5))
        State.hud.add('Collapse Level', Statf(State.hud.next_pos(),
            'Collapse %s', callback=lambda:'%s'%str(State.map.current.collapse_level), interval=.5))
        
        State.speed = 3.33
    
    def update(self, dt):
        if self.movex or self.movey:
            r = State.camera.rect.move(self.movex,self.movey)
            r.clamp_ip(State.map.rect)
            State.camera.position = r.center
        State.camera.update(dt)
        State.map.update(dt)
        State.hud.update(dt)
    
    def draw(self, interp):
        State.screen.clear()
        State.map.draw()
        State.hud.draw()
        State.screen.flip()
    
    def on_key_down(self, unicode, key, mod):
        if key == K_DOWN: self.movey += State.speed
        elif key == K_UP: self.movey += -State.speed
        elif key == K_RIGHT: self.movex += State.speed
        elif key == K_LEFT: self.movex += -State.speed
        elif key in (COLLAPSE_KEYS):
            clevel = key - K_0
            for mh in State.map.handlers.values():
                mh.collapse(clevel)
        elif key == K_ESCAPE: context.pop()
    
    def on_key_up(self, key, mod):
        if key == K_DOWN: self.movey -= State.speed
        elif key == K_UP: self.movey -= -State.speed
        elif key == K_RIGHT: self.movex -= State.speed
        elif key == K_LEFT: self.movex -= -State.speed
    
    def on_quit(self):
        context.pop()


class TiledMapHandler(MapHandler):
    
    # 4 gives better FPS at resolution 320x320, but can cause loading hiccups
    # 2 gives smoothest loading, highest cache hits
    collapse_level = (4,4)
    
    def load(self):
        self.map = TiledMap(
            data.filepath('map',self.map_file), collapse=self.collapse_level)
    
    def collapse(self, clevel):
        if clevel > (1,1):
            self.collapse_level = clevel
            # self.map could be None if the map isn't loaded or has been
            # unloaded.
            if self.map:
                self.map.collapse(clevel)


def make_supermap(app):
    # Make a 9x9 supermap, using the same map file for each.
    #map_filename = 'Gumm multi layer.tmx'
    map_filename = 'Gumm super desert.tmx'
    app.map = State.map = SuperMap()
    for n in ((0,0),) + supermap.NEIGHBORS:
        app.map.add_handler(TiledMapHandler(n, map_filename))
    app.world = State.world = model.NoWorld(app.map.rect)


def main():
    app = App()
    gummworld2.run(app)


if __name__ == '__main__':
    if False:
        cProfile.run('main()', 'prof.dat')
        p = pstats.Stats('prof.dat')
        p.sort_stats('time').print_stats()
    else:
        main()
