import pygame
from math import floor


class SubPixelSurface(object):

    def __init__(self, surface, level=3):

        """Creates a sub pixel surface object.

        surface -- A PyGame surface
        x_level -- Number of sub-pixel levels in x
        y_level -- Number of sub-pixel levels in y (same as x if omited)

        """

        self.level = level

        x_steps = [float(n) / self.level for n in xrange(self.level)]
        y_steps = [float(n) / self.level for n in xrange(self.level)]

        self.surfaces = []
        for frac_y in y_steps:
            row = []
            self.surfaces.append(row)
            for frac_x in x_steps:
                row.append( SubPixelSurface._generate(surface.copy(), frac_x, frac_y, level) )


    @staticmethod
    def _generate(orig_surf, frac_x, frac_y, level):

        surf_x = int( frac_x * level )
        surf_y = int( frac_y * level )

        orig_w, orig_h = orig_surf.get_size()
        surf = pygame.Surface((orig_w+2, orig_h+2), pygame.SRCALPHA)
        surf.fill((0,0,0,0))
        surf.blit(orig_surf, (1,1), None, pygame.BLEND_RGBA_ADD)
        orig_surf = surf

        assert surf_x < level and surf_y < level

        orig_w, orig_h = orig_surf.get_size()
        w = level * orig_w
        h = level * orig_h
        s = pygame.transform.smoothscale(orig_surf, (w, h))

        surf = pygame.Surface((w + level, h + level), pygame.SRCALPHA)
        surf.fill((0,0,0,0))

        surf.blit(s, (surf_x, surf_y), None, pygame.BLEND_RGBA_ADD)

        # surf = pygame.transform.smoothscale(surf, (orig_w + 1, orig_h + 1))
        surf = pygame.transform.smoothscale(surf, (orig_w + 0, orig_h + 0))

        return surf
    
    
    def at(self, x, y):

        """Gets a sub-pixel surface for a given coordinate.

        x -- X coordinate
        y -- Y coordinate

        """

        surf_x = int( (x - floor(x)) * self.level )
        surf_y = int( (y - floor(y)) * self.level )

        return self.surfaces[surf_y][surf_x]
