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


"""game_clock.py - Game clock for Gummworld2.

The inspiration for this module came from Koen Witters's superb article
"deWiTTERS Game Loop", aka "Constant Game Speed independent of Variable FPS" at
http://www.koonsolo.com/news/dewitters-gameloop/.

Pythonated by Gummbum. While the demo requires Pygame, the module does not. The
GameClock class is purely Python and should be compatible with other Python-
based multi-media and game development platforms.

Note that Python Library docs mention that time.clock() does not return
fractions of a second on all computer platforms. Therefore this module will not
work on such platforms.
"""

import time

class GameClock(object):
    """Run game engine at a constant game speed independent of variable FPS.
    Parameters:
        ticks_per_second -> Positive integer. Constant ticks per second for
            game physics.
        max_fps -> Positive integer. Max frames allowed per second. A value of
            zero allows unlimited frames.
        use_wait -> Boolean. When True, GameClock.tick() uses time.sleep to
            throttle frames per second. This uses less CPU at the postential
            cost of smoothness. When False, GameClock.tick() returns without
            injecting any waits, and can result in smoother frames.
        max_frame_skip -> Positive integer. Max game ticks allowed before
            forcing a frame display.
    Properties:
        ticks_per_second -> Read-write. See parameter ticks_per_second.
        max_fps -> Read-write. See parameter max_fps.
        use_wait -> Read-write. See parameter use_wait.
        max_frame_skip -> Read-write. See parameter max_frame_skip.
    Methods:
        tick() -> Game loop timer. Call once per game loop.
        get_time() -> Return the milliseconds elapsed in the previous call to tick().
        get_fps() -> Return the frame rate from the previous second.
        get_ups() -> Return the update rate from the previous second.
        interpolate() -> Return float (range 0 to 1) as prediction factor.
        update_ready() -> Return boolean indicating if game should be updated.
        frame_ready() -> Return boolean indicating if display should be updated.
        reset() -> Reset clock counters.
    """
    
    def __init__(self, ticks_per_second=25, max_fps=0, use_wait=True, max_frame_skip=5):
        self._wait = time.sleep
        self._get_ticks = time.clock
        self.ticks_per_second = ticks_per_second
        self.max_fps = max_fps
        self.use_wait = use_wait
        self.max_frame_skip = 5
        self.reset()
        
    def reset(self):
        """Reset clock counters."""
        self._tick_size = 1.0 / self.ticks_per_second
        self._reset_threshold = 1.0 + self._tick_size
        self._ticks = 0
        self._next_game_tick = self._get_ticks()
        self._next_frame = self._get_ticks()
        self._loops = 0
        self._update_ready = False
        self._frame_ready = False
        #
        self._time = self._get_ticks()
        self._elapsed = 0
        self._tps = 0.0
        self._frame_count = 0
        self._fps = 0
        self._update_count = 0
        self._ups = 0
    
    @property
    def ticks_per_second(self):
        """Get or set ticks per second."""
        return self._ticks_per_second
    @ticks_per_second.setter
    def ticks_per_second(self, n):
        if n > 0:
            self._ticks_per_second = n
        else:
            self._ticks_per_second = 25
        self._skip_ticks = 1.0 / self._ticks_per_second
        self.reset()
    
    @property
    def max_fps(self):
        """Get or set max_fps."""
        return self._max_fps
    @max_fps.setter
    def max_fps(self, n):
        if n > 0:
            self._max_fps = n
            self._skip_frames = 1.0 / n
        else:
            self._max_fps = 0
            self._skip_frames = 0
        self.reset()
    
    @property
    def use_wait(self):
        """Get or set use_wait."""
        return self._use_wait
    @use_wait.setter
    def use_wait(self, enabled):
        self._use_wait = enabled
        self._tps = float(self.max_fps)

    @property
    def max_frame_skip(self):
        """Get or set max_frame_skip."""
        return self._max_frame_skip
    @max_frame_skip.setter
    def max_frame_skip(self, n):
        if n > 0:
            self._max_frame_skip = n
        else:
            self._max_frame_skip = 0
        self.reset()

    def update_ready(self):
        """Call once per game loop. If True is returned, update the game physics."""
        return self._update_ready
    
    def frame_ready(self):
        """Call once per game loop. If True is returned, display a graphics frame."""
        return self._frame_ready

    def _flip(self):
        """Update runtime stats and counters every second."""
        time = self._get_ticks()
        self._ticks = time - self._time
        self._elapsed += self._ticks
        self._time = time
        # Once per second...
        if self._elapsed < 1:
            return
        elif self._elapsed >= self._reset_threshold:
            self.reset()
        else:
            self._elapsed %= 1
        # Save stats and clear counters.
        self._tps = 0.0
        self._fps = self._frame_count
        self._ups = self._update_count
        self._frame_count = self._update_count = 0

    def tick(self):
        """Game loop timer. Call once per game loop to calculate runtime values.
        After calling, check the update_ready() and frame_ready() methods.
        Sleep cycles are injected if use_wait=True. Returns the number of
        milliseconds that have elapsed since the last call to tick()."""
        self._tps += 1
        self._flip()
        self._update_ready = self._frame_ready = False
        if self._get_ticks() > self._next_game_tick and \
            self._loops < self.max_frame_skip:
            self._update_count += 1
            self._next_game_tick += self._skip_ticks
            self._loops += 1
            self._update_ready = True
        if self._get_ticks() > self._next_frame or \
            self._loops >= self.max_frame_skip:
            self._frame_count += 1
            self._next_frame += self._skip_frames
            self._loops = 0
            self._frame_ready = True
        elif self._use_wait and self.max_fps > 0:
# This code produced glitches, especially as FPS approaches TPS.
#            ms = self._tps / self.max_fps
#            if round(ms) >= 2:
#                self._wait(ms/1000)
# The following is more straightforward and introduces only one fairly accurate
# wait for each frame.
            wait_ms = float(self._next_frame) - self._get_ticks()
            self._wait(wait_ms/1000.0)
        return self._ticks

    def interpolate(self):
        """Return a float representing the current position in between the
        previous gametick and the next one. This allows the main game loop to
        make predictive calculations between gameticks."""
        return (
            self._get_ticks() + self._skip_ticks - self._next_game_tick
        ) / self._skip_ticks
    
    def get_time(self):
        """Return the milliseconds elapsed in the previous call to tick()."""
        return self._ticks

    def get_fps(self):
        """Return frames per second during the previous second."""
        return self._fps
    
    def get_ups(self):
        """Return updates per second during the previous second."""
        return self._ups

if __name__ == '__main__':
    """
    USAGE TIPS

    When first trying this demo follow these steps. These tips assume the
    stock (unmodified) settings are used.

        1.  Initially the game uses a Pygame clock loop, unthrottled. Use this
            mode to compare the maximum frame rate between this mode and the
            GameClock loop. Press the M key to toggle frame rate throttling.
        2.  Press the M key to throttle Pygame to 30 FPS. This is the typical
            method employed in Pygame to fix the rate of game ticks.
        3.  Press the L key to swith to GameClock loop. Note the UPS (updates
            per second) are 30, as with the Pygame clock. The frame rate should
            be much higher, and the motion of the balls should be smoother.
        4.  Press the Tab key to cycle GameClock to the next settings, which
            throttle the frame rate at 120 per second. Switch between Pygame and
            GameClock with the L key and compare the smoothness of the motion.
        5.  In GameClock mode with a CPU meter running press the W key to toggle
            Wait (GameClock uses time.wait()) and watch the effect on CPU usage.
        6.  Press the Tab key to watch how smoothness of motion is affected when
            the GameClock frame rate is throttled to 60 FPS, and again at 30.
            Note that at 30 FPS there is no apparent difference between
            GameClock and Pygame.
        7.  Press the Tab key again to view GameClock throttled to 6 UPS. Ball
            class implements two kinds of prediction: motion, and screen edge
            collision. Use the P key to toggle screen edge prediction. Note
            that when Predict is on the balls behave well when colliding with
            screen edges. When Predict is off predict() assumes it will never
            change course, and update() snaps it back from the predicted
            position. The effect is visually jarring, and is visible even at
            higher frame rates.
        8.  Pressing K toggles whether collisions kill balls. It does not
            toggle collision detection. There is no appreciable difference here
            between Pygame and GameClock.
        9.  Pressing B creates 25 more balls.
        10. There are a couple gotchas with GameClock that have been called out
            in code comments. See update_gameclock().

    ABOUT THE DEMO
    
    This demo sends a ball careening about the window. It is probably not the
    best usage for the GameClock class, but it provides a good basis for
    demonstrating linear motion prediction, and salving an eyesore with some
    judicious collision prediction.
    
    You could certainly use the GameClock simply as a timer and FPS throttle,
    but that only scratches the surface.
    
    With an implementation like this demo you're deciding you want to update
    some visual aspects of the game as often as possible, while time passes at a
    slower, constant rate for the game mechanics. This is done by separating the
    game mechanics routine from the display routine and calling them on
    independent cycles. If the game mechanics are comparatively more costly in
    computing power, there is potentially a lot of benefit in choosing to update
    the mechanics at a much lower rate than updating frames for display.

    Of course, in order to update the display meaningfully you need to modify
    it. Otherwise you're seeing the same image posted repeatedly. But if the
    display changes are waiting on game mechanics to post, you can only update
    the display as fast as you can compute the entire world. This is where
    prediction fits in: updating the display in advance of the game mechanics.

    The design problem is what do you predict? First, it should make a positive
    difference in the user experience. Second, the more you add to your display
    computation the lower your frame rate.

    There are two kinds of prediction Ball can use: motion and collision. Once
    we start predicting the motion we notice that when the ball collides with
    the screen edge the rebound jars the eye. This is because simple motion
    prediction assumes there will be no course changes and overshoots the edge.
    In most cases the prediction is right, but in edge collision it is wrong,
    and the next update snaps it back from the predicted position.
    
    If this were invisible it wouldn't be a problem. Rather it is quite
    annoying. The problem can be solved by predicting collisions, making
    update() and predict() adjust their calculations by the interpolation value
    at the time the collision occurred. And we see the ill effect is resolved
    when we turn on screen-edge collision prediction (enabling with the P key).
    
    A notable distinction is there are two collision conditions that change the
    ball's behavior: collision with the screen edges and collision with another
    ball. The distinction is that predicting screen edge collision makes a
    visible difference.
    
    By contrast, when two balls collide it does not visually matter whether they
    react immediately or there is a delay, even at a very low 6 updates-per-
    second. Therefore, the potentially expensive ball-vs-ball collision
    detection can be done less frequently. Of course, if you're shooting very
    fast bullets it would matter, but that doesn't apply to our demo.
    
    Ultimately the choice of what to predict and what to defer is a project
    decision. Hopefully this explanation has illuminated the reasoning used in
    designing the demo's prediction capabilities and has shown that if done
    intelligently, such tricks can add virtual performance to your application.

    THE INTERFACE

    Input keys:
        L -> Loop; Toggle between Pygame and GameClock timed loops.
        Tab:[TicksPerSecond MaxFPS] -> Cycle through the GameClock settings.
        K -> Kill; Toggle whether collisions kill balls.
        M -> MaxFPS; Toggle Pygame clock's MaxFPS throttle.
        P -> Predict; Toggle whether the ball uses its GameClock predictive algorithm.
        W -> Wait; Toggle whether GameClock uses time.sleep().
        B -> Balls; Make 25 more balls.
    
    The title bar displays the runtime settings and stats. If the stats are
    chopped off you can increase the window width in main().
    
    Stats:
        Runtime:[FPS=%d UPS=%d] -> The number of frames and updates that
            occurred during the previous second.
    """
    import random
    import pygame
    from pygame.locals import (
        Color, QUIT, KEYDOWN, K_ESCAPE, K_TAB, K_1, K_b, K_k, K_l, K_m, K_p, K_w,
    )
    # GameClock control.
    TICKS_PER_SECOND = 30.0
    MAX_FRAME_SKIP = 5.0
    # Ball control.
    MAX_BALL_SPEED = 240.0  # pixels per second
    INIT_BALLS = 100        # initial number of balls
    ## Note to tweakers: Try adjusting these GameClock settings before adjusting
    ## the fundamental ones above.
    SETTINGS = (
        # TicksPerSecond   MaxFPS
        (TICKS_PER_SECOND, 0),                  # unlimited FPS
        (TICKS_PER_SECOND, MAX_BALL_SPEED/2),   # max FPS is half ball speed
        (TICKS_PER_SECOND, TICKS_PER_SECOND*2), # max FPS is double TPS
        (TICKS_PER_SECOND, TICKS_PER_SECOND),   # max FPS is TPS
        (TICKS_PER_SECOND/5, 0),                # TPS is 6; unlimited FPS
    )
    # Use Pygame clock, or GameClock.
    USE_PYGAME_CLOCK = True
    PYGAME_FPS = 0
    # Ball uses prediction? Enable this to see how combining interpolation and
    # prediction can smooth frames between updates, and solve visual artifacts.
    USE_PREDICTION = True
    # Balls are killed when they collide.
    DO_KILL = False
    # Appearance.
    BGCOLOR = Color(175,125,125)
    ## NO MORE CONFIGURABLES.
    # Game objects.
    elapsed = 0
    game_ticks = 0
    pygame_clock = None
    clock = None
    screen = None
    screen_rect = None
    eraser_image = None
    sprite_group = None
    
    def logger(*args):
        if logging: print ' '.join([str(a) for a in args])
    logging = True
    
    class Ball(pygame.sprite.Sprite):
        size = (40,40)
        def __init__(self):
            pygame.sprite.Sprite.__init__(self)
            self.image = pygame.surface.Surface(self.size)
            self.rect = self.image.get_rect()
            self._detail_block(self.image, Color('red'), self.rect)
            w,h = screen_rect.size
            self.x = float(random.randrange(self.size[0],w-self.size[0]))
            self.y = float(random.randrange(self.size[1],h-self.size[1]))
            self.rect.center = round(self.x),round(self.y)
            self.dx = random.choice([-1,1])
            self.dy = random.choice([-1,1])
            # Speed is pixels per second.
            self.speed = MAX_BALL_SPEED
            ## These prorate the speed step made in update() by remembering the
            ## interpolation value when a screen edge collision occurs. This
            ## removes all occurrence of twitchy rebounds.
            self.predictive_rebound_x = 0.0
            self.predictive_rebound_y = 0.0
        def _dim(self, color, frac):
            c = Color(*color)
            c.r = int(round(c.r*frac))
            c.g = int(round(c.g*frac))
            c.b = int(round(c.b*frac))
            return c
        def _detail_block(self, image, color, rect):
            image.fill(self._dim(color,0.6))
            tl,tr = (0,0),(rect.width-1,0)
            bl,br = (0,rect.height-1),(rect.width-1,rect.height-1)
            pygame.draw.lines(image, color, False, (bl,tl,tr))
            pygame.draw.lines(image, self._dim(color,0.3), False, (tr,br,bl))
        def update(self, *args):
            """Call once per tick to update state."""
            ## If prediction is enabled then predict() handles rebounds.
            use_prediction = list(args).pop(0)
            if not use_prediction:
                self._rebound(0.0)
            ## Speed step needs to be adjusted by the value of interpolation
            ## at the time the ball collided with an edge (predictive_rebound_*).
            self.x += self.dx * self.speed/TICKS_PER_SECOND * (1-self.predictive_rebound_x)
            self.y += self.dy * self.speed/TICKS_PER_SECOND * (1-self.predictive_rebound_y)
            self.predictive_rebound_x,self.predictive_rebound_y = 0.0,0.0
            self.rect.center = round(self.x),round(self.y)
        def predict(self, interpolation, use_prediction):
            """Call as often as you like. Hitting the edge is predicted, and the
            ball's direction is changed appropriately."""
            ## If prediction is not enabled then update() handles rebounds.
            if use_prediction:
                self._rebound(interpolation)
            ## Interpolation needs to be adjusted by the value of interpolation
            ## at the time the ball collided with an edge (predictive_rebound_*).
            x = self.x + self.dx * self.speed/TICKS_PER_SECOND * (interpolation-self.predictive_rebound_x)
            y = self.y + self.dy * self.speed/TICKS_PER_SECOND * (interpolation-self.predictive_rebound_y)
            self.rect.center = round(x),round(y)
        def _rebound(self, interpolation):
            ## 1. Handle screen edge collisions.
            ## 2. Update the prediction_rebound_* adjusters.
            r = self.rect
            if r.left < screen_rect.left:
                r.left = screen_rect.left
                self.x = float(r.centerx)
                self.dx = -self.dx
                self.predictive_rebound_x = interpolation
            elif r.right >= screen_rect.right:
                r.right = screen_rect.right-1
                self.x = float(r.centerx)
                self.dx = -self.dx
                self.predictive_rebound_x = interpolation
            if r.top < screen_rect.top:
                r.top = screen_rect.top
                self.y = float(r.centery)
                self.dy = -self.dy
                self.predictive_rebound_y = interpolation
            elif r.bottom >= screen_rect.bottom:
                r.bottom = screen_rect.bottom-1
                self.y = float(r.centery)
                self.dy = -self.dy
                self.predictive_rebound_y = interpolation

    def update_pygame():
        """Update function for use with Pygame clock."""
        global elapsed
        sprite_group.update(False)
        handle_collisions()
        elapsed += pygame_clock.get_time()
        if elapsed >= 1000:
            set_caption()
            elapsed -= 1000

    def display_pygame():
        """Display function for use with Pygame clock."""
        sprite_group.clear(screen, eraser_image)
        sprite_group.draw(screen)
        pygame.display.update()

    def update_gameclock():
        """Update function for use with GameClock."""
        global game_ticks
        ## GOTCHA: Both Ball.update() and Ball.predict() modify sprite
        ## position, so the update and display routines must each perform
        ## erasure. This results in redundant erasures whenever an update and
        ## frame are ready in the same pass. This happens almost every game tick
        ## at high frame rates, often enough that an avoidance optimization
        ## would gain a few FPS.
        sprite_group.clear(screen, eraser_image)
        sprite_group.update(USE_PREDICTION)
        handle_collisions()
        game_ticks += 1
        if game_ticks >= clock.ticks_per_second:
            set_caption()
            game_ticks = 0

    def display_gameclock(interpolation):
        """Display function for use with GameClock."""
        ## GOTCHA: See the comment in update_gameclock().
        sprite_group.clear(screen, eraser_image)
        for ball in sprite_group:
            ball.predict(interpolation, USE_PREDICTION)
        sprite_group.draw(screen)
        pygame.display.update()

    def handle_collisions():
        """Handle collisions for both Pygame clock and GameClock."""
        for sprite in sprite_group:
            for other in pygame.sprite.spritecollide(sprite, sprite_group, False):
                if sprite is not other and DO_KILL:
                    sprite.kill()
                    other.kill()

    def set_caption():
        """Set window caption for both Pygame clock and GameClock."""
        if USE_PYGAME_CLOCK:
            pygame.display.set_caption(
                'Loop=Pygame Kill=%s MaxFPS=%d Runtime:[FPS=%d Balls=%d]' % (
                DO_KILL, PYGAME_FPS, pygame_clock.get_fps(), len(sprite_group)))
        else:
            pygame.display.set_caption(
                ' '.join(('Loop=GameClock Tab:[TPS=%d MaxFPS=%d] Predict=%s Wait=%s Kill=%s',
                         'Runtime:[FPS=%d UPS=%d Balls=%d]')) % (
                clock.ticks_per_second, clock.max_fps, USE_PREDICTION, clock.use_wait,
                DO_KILL, clock.get_fps(), clock.get_ups(), len(sprite_group)))

    def main():
        global clock, pygame_clock, screen, screen_rect, sprite_group, eraser_image
        global USE_PYGAME_CLOCK, DO_KILL, USE_PREDICTION, PYGAME_FPS
        screen = pygame.display.set_mode((800,600))
        screen.fill(BGCOLOR)
        screen_rect = screen.get_rect()
        eraser_image = screen.copy()
        which_settings = 0
        pygame_clock = pygame.time.Clock()
        clock = GameClock(*SETTINGS[which_settings])
        clock.use_wait = False
        sprite_group = pygame.sprite.Group([Ball() for i in range(INIT_BALLS)])
        #
        game_is_running = True
        while game_is_running:
            if USE_PYGAME_CLOCK:
                pygame_clock.tick(PYGAME_FPS)
                update_pygame()
                display_pygame()
            else:
                clock.tick()
                if clock.update_ready():
                    update_gameclock()
                if clock.frame_ready():
                    display_gameclock(clock.interpolate())
            #
            for e in pygame.event.get():
                if e.type == QUIT: quit()
                elif e.type == KEYDOWN:
                    if e.key == K_ESCAPE: quit()
                    elif e.key == K_TAB:
                        which_settings += 1
                        if which_settings >= len(SETTINGS):
                            which_settings = 0
                        (clock.ticks_per_second,clock.max_fps) = SETTINGS[which_settings]
                    elif e.key == K_1:
                        sprite_group.add(Ball())
                    elif e.key == K_b:
                        sprite_group.add([Ball() for i in range(25)])
                    elif e.key == K_k:
                        DO_KILL = not DO_KILL
                    elif e.key == K_l:
                        USE_PYGAME_CLOCK = not USE_PYGAME_CLOCK
                    elif e.key == K_m:
                        if PYGAME_FPS == 0:
                            PYGAME_FPS = 30
                        else:
                            PYGAME_FPS = 0
                    elif e.key == K_p:
                        USE_PREDICTION = not USE_PREDICTION
                    elif e.key == K_w:
                        clock.use_wait = not clock.use_wait
    
    pygame.init()
    main()
