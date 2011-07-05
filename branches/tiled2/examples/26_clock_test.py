import pygame
from pygame.locals import *

import paths
import gummworld2
from gummworld2 import (
    Engine,
    State,
)


class Meter(object):
    """Yer basic countdown meter."""
    
    def __init__(self, rect, color, min_val, max_val, init_val):
        self.rect = Rect(rect)
        self.fill_rect = Rect(self.rect)
        self.color = color
        self.min_val = min_val
        self.max_val = max_val
        self.val = init_val
    
    def fire(self, dt):
        """Callback invoked by the clock."""
        self.fill_rect.w = self.rect.w
        self.val = self.max_val
    
    def update(self, dt):
        """Update the progress value and fill rect."""
        self.val -= dt
        if self.val < self.min_val:
            self.val = self.min_val
        self.fill_rect.w = self.rect.w * self.val / (self.max_val-self.min_val)
    
    def draw(self, dt, surf):
        """Draw the meter."""
        surf.fill((0,0,0), self.rect)
        pygame.draw.rect(surf, self.color, self.rect, 1)
        surf.fill(self.color, self.fill_rect)


class App(Engine):
    
    def __init__(self):
        Engine.__init__(self,
            resolution=(640,480),
            update_speed=30, frame_speed=0,
            default_schedules=False,
        )
        
        self.paused = False
        pygame.display.set_caption('RUNNING - Mouse Click: Pause/Resume')
        
        # Make meters and schedule them to fire.
        self.meters = []
        w,h = self.screen.width-128,20
        x = 64
        for y in range(1,10):
            y = float(y)
            c = int(255 * y / 10)
            meter = Meter((x,30*y,w,h), Color(c,c,255), 0., y, y)
            self.clock.schedule_interval(meter.fire, y)
            self.meters.append(meter)
    
    def run_paused(self):
        """Process events and redraw the view while clock is paused."""
        while self.paused:
            pygame.time.wait(40)
            self._get_events(0)
            self.draw(0)
    
    def pause(self):
        """Enter paused state."""
        pygame.display.set_caption('PAUSED')
        self.clock.pause()
        self.paused = True
        self.run_paused()
    
    def resume(self):
        """Exit paused state."""
        pygame.display.set_caption('RESUMED')
        self.clock.resume()
        self.paused = False
    
    def draw(self, dt):
        """Draw the view."""
        surf = self.screen.surface
        for meter in self.meters:
            meter.update(dt)
            meter.draw(dt, surf)
        self.screen.flip()
    
    def on_key_down(self, unicode, key, mod):
        if key == K_ESCAPE:
            quit()
    
    def on_mouse_button_down(self, pos, button):
        if self.paused:
            self.resume()
        else:
            self.pause()
    
    def on_quit(self):
        quit()


if __name__ == '__main__':
    app = App()
    gummworld2.run(app)
