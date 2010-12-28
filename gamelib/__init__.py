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


__version__ = '0.2'
__vernum__ = (0,2)


"""__init__.py - Package initializer for Gummworld2.
"""


import pygame
import pymunk

pygame.init()
pymunk.init_pymunk()

# Classes
from vec2d import Vec2d
from state import State

from camera import Camera
from map import Map
from game_clock import GameClock
from graphics import Graphics
from popup_menu import PopupMenu
from ui import HUD, Stat, Statf

from engine import Engine

# Modules
import model
import view
import data
import geometry
import pygame_utils
import popup_menu
import ui
import toolkit
