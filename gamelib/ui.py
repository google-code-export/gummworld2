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


__version__ = '0.4'
__vernum__ = (0,4)


__doc__ = """ui.py - User Interface module for Gummworld2.

Currently there is only HUD. And some dynamic stats classes with timers for
callback.
"""


import time

import pygame
from pygame.locals import Color, RLEACCEL

from gamelib import data, State


pygame.init()
hud_font = pygame.font.Font(data.filepath('font', 'Vera.ttf'), 10)
hud_alpha = 208
text_color = Color('yellow')


class HUD(pygame.sprite.OrderedUpdates):
    
    def __init__(self):
        super(HUD, self).__init__()
        self.stats = {}
        self.top = 5
        self.font_height = hud_font.get_height()
        self.y = lambda n: self.top + self.font_height * n
        self.x = State.screen.rect.x + 5
        self.i = 0

    def next_pos(self):
        i = self.i
        self.i += 1
        return self.x, self.y(i)

    def add(self, *args):
        """args: name, stat"""
        if args:
            name,stat = args[0:2]
            self.stats[name] = stat
            super(HUD, self).add(stat)
    
    def remove(self, *sprites):
        """remove sprites by name or sprite object"""
        for sprite in sprites:
            if isinstance(sprite, str):
                name = sprite
                sprite = self.stats[sprite]
                del self.stats[name]
            else:
                for key,value in self.stats.items():
                    if value is sprite:
                        del self.stats[key]
            super(HUD, self).remove(sprite)

    def update(self):
        for stat in self.stats.values():
            stat.update()

    def draw(self, surface=None):
        if not State.show_hud:
            return
        if surface is None:
            super(HUD, self).draw(State.camera.surface)
        else:
            super(HUD, self).draw(surface)


class Stat(pygame.sprite.Sprite):
    """a HUD stat with plain string"""
    
    def __init__(self, pos, text=None, callback=None, interval=2000):
        pygame.sprite.Sprite.__init__(self)
        self.font = hud_font
        self.text = None
        self.callback = callback
        self.interval = interval
        self.next_time = pygame.time.get_ticks()
        if text is not None:
            self.set_value(text)
        elif callback:
            self.update()
        self.rect = self.image.get_rect()
        self.rect.topleft = pos

    def update(self, *args):
        if self.callback:
            now = pygame.time.get_ticks()
            if self.next_time <= now:
                self.set_value(self.callback())
                self.next_time = now + self.interval
    
    def set_value(self, text):
        if isinstance(text, str) and text != self.text:
            self.text = text
            self.image = self.font.render(text, True, text_color)
            self.image.set_alpha(hud_alpha)


class Statf(pygame.sprite.Sprite):
    """a HUD stat with formatted string"""
    
    def __init__(self, pos, fmt, value=None, callback=None, interval=2000):
        pygame.sprite.Sprite.__init__(self)
        self.font = hud_font
        self.fmt = fmt
        self.value = None
        self.callback = callback
        self.interval = interval
        self.next_time = pygame.time.get_ticks()
        if value is not None:
            self.set_value(value)
        elif callback:
            self.update()
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
    
    def update(self, *args):
        if self.callback:
            now = pygame.time.get_ticks()
            if self.next_time <= now:
                self.set_value(self.callback())
                self.next_time = now + self.interval
    
    def set_value(self, value):
        if value is not None and value != self.value:
            self.value = value
            self.image = self.font.render(self.fmt%(value,), True, text_color)
            self.image.set_alpha(hud_alpha)

if __name__ == '__main__':
    screen = pygame.display.set_mode((600,600))
    clock = pygame.time.Clock()
    left = 20
    top = 20
    height = hud_font.get_height()
    hud = HUD()
    y = lambda n: top+height*n
    hud.add('stat1', Stat((left,y(0)), 'Stat 1'))
    hud.add('time', Statf((left,y(1)), 'Time %d', callback=time.time, interval=100))
    hud.add('fps', Statf((left,y(2)), 'FPS %d', callback=clock.get_fps))
    while 1:
        clock.tick()
        screen.fill((0,0,0))
        hud.update()
        hud.draw(screen)
        pygame.display.flip()
        pygame.event.get()
