import cProfile, pstats

import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import Engine, State, TiledMap
from gummworld2 import context, data, toolkit, ui


class App(Engine):
    
    def __init__(self):
        resolution = 640,480
        map = TiledMap(
            data.filepath('map', 'Gumm no swamps.tmx'),
            collapse_level=8,
        )
        self.movex = 0
        self.movey = 0
        self.visible_tiles = []
        
        Engine.__init__(self,
            resolution=resolution,
            map=map,
            frame_speed=0,
        )
        self.camera.init_position(self.screen.center)
        toolkit.make_hud()
        State.clock.schedule_update_priority(State.hud.update, 1.0)
    
    def update(self, dt):
        if self.movex or self.movey:
            State.camera.position += self.movex,self.movey
    
    def draw(self, dt):
        State.screen.clear()
        self.draw_tiles()
        State.hud.draw()
        State.screen.flip()
    
    def draw_tiles(self):
        map = State.map
        renderer = map.renderer
        cam = State.camera
        camx,camy = cam.rect.center
        w,h = State.screen.size
        renderer.set_camera_position(camx, camy, w, h, 3)
        surf = cam.surface
        for layer in map.get_tile_layers():
            renderer.render_layer(surf, layer, False)
    
    def on_key_down(self, unicode, key, mod):
        if key == K_DOWN: self.movey += State.speed
        elif key == K_UP: self.movey += -State.speed
        elif key == K_RIGHT: self.movex += State.speed
        elif key == K_LEFT: self.movex += -State.speed
        elif key == K_ESCAPE: context.pop()
    
    def on_key_up(self, key, mod):
        if key == K_DOWN: self.movey -= State.speed
        elif key == K_UP: self.movey -= -State.speed
        elif key == K_RIGHT: self.movex -= State.speed
        elif key == K_LEFT: self.movex -= -State.speed
    
    def on_quit(self):
        context.pop()


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
