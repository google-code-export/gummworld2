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


"""__init__.py - Package initializer for Gummworld2.
"""

__doc__="""
Gummworld2 is designed as a light pygame framework for a scrolling game, where
the map is larger than the display. It emphasizes simplicity, freedom, and
performance.
"""


try:
    import pymunk
except:
    print 'pymunk not found: proceeding without'
else:
    pymunk.init_pymunk()

import pygame
pygame.init()

from gummworld2 import version
if __debug__: print 'gummworld2 v%s loading...' % version.version

# Classes
from vec2d import Vec2d
from state import State
from context import Context
from subpixel import SubPixelSurface

# the following creates a separate namespace, don't do it.
#from tiledtmxloader.tiledtmxloader import TileMap, TileMapParser
#from tiledtmxloader.helperspygame import ResourceLoaderPygame, RendererPygame

from screen import Screen, View
from map import Map, MapLayer
from tiledmap import TiledMap
from quadtree import QuadTree
from supermap import SuperMap, MapHandler
from camera import Camera
from gameclock import GameClock
from popup_menu import PopupMenu
from ui import HUD, Stat, Statf
from canvas import Canvas
from sprite import CameraTargetSprite, BucketSprite, BucketGroup

from engine import run, Engine, NO_WORLD, SIMPLE_WORLD, QUADTREE_WORLD, PYMUNK_WORLD


# Toolkits and utilities
import context
import model
import data
import geometry
import pygame_utils
import popup_menu
import state
import ui
import toolkit
import quadtree
import supermap

if __debug__: print 'gummworld2 v%s loaded' % version.version
