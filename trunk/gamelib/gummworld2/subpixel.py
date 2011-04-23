import pygame
from math import floor


class SubPixelSurface(object):

    def __init__(self, surface, x_level=3, y_level=None):

        """Creates a sub pixel surface object.

        surface -- A PyGame surface
        x_level -- Number of sub-pixel levels in x
        y_level -- Number of sub-pixel levels in y (same as x if omited)

        """

        self.x_level = x_level
        self.y_level = y_level or x_level

        x_steps = [float(n) / self.x_level for n in xrange(self.x_level)]
        y_steps = [float(n) / self.y_level for n in xrange(self.y_level)]

        self.surfaces = []
        for frac_y in y_steps:
            row = []
            self.surfaces.append(row)
            for frac_x in x_steps:
                row.append( SubPixelSurface._generate(surface.copy(), frac_x, frac_y) )


    @staticmethod
    def _generate(s, frac_x, frac_y):
        frac_x = 1. - frac_x

        sa = (1.-frac_x) * (1.-frac_y)
        sb = (1.-frac_x) * frac_y
        sc = frac_x * (1.-frac_y)
        sd = (frac_x * frac_y)

        assert round(sa + sb + sc + sd, 6) == 1.0

        w, h = s.get_size()
        surf = pygame.Surface((w+1, h+1), pygame.SRCALPHA)
        # black, fully transparent surface
        surf.fill((0, 0, 0, 0))

        ss = s.copy()
        pc = int( round(sc * 255.0 ))
        # make alpha adjustment on every pixel
        ss.fill((pc, pc, pc, pc), None, pygame.BLEND_RGBA_MULT)
        # add that result to the black surface
        surf.blit(ss, (0, 0), None, pygame.BLEND_RGBA_ADD)

        ss = s.copy()
        pc = int( round(sa * 255.0 ))
        # make alpha adjustment on every pixel
        ss.fill((pc, pc, pc, pc), None, pygame.BLEND_RGBA_MULT)
        # add that result to the black surface
        surf.blit(ss, (1, 0), None, pygame.BLEND_RGBA_ADD)

        ss = s.copy()
        pc = int( round(sd * 255.0 ))
        # make alpha adjustment on every pixel
        ss.fill((pc, pc, pc, pc), None, pygame.BLEND_RGBA_MULT)
        # add that result to the black surface
        surf.blit(ss, (0, 1), None, pygame.BLEND_RGBA_ADD)

        ss = s.copy()
        pc = int( round(sb * 255.0 ))
        # make alpha adjustment on every pixel
        ss.fill((pc, pc, pc, pc), None, pygame.BLEND_RGBA_MULT)
        # add that result to the black surface
        surf.blit(ss, (1, 1), None, pygame.BLEND_RGBA_ADD)

        return surf


    def at(self, x, y):

        """Gets a sub-pixel surface for a given coordinate.

        x -- X coordinate
        y -- Y coordinate

        """

        surf_x = int( (x - floor(x)) * self.x_level )
        surf_y = int( (y - floor(y)) * self.y_level )

        return self.surfaces[surf_y][surf_x]
