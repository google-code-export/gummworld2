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


__doc__ = """context.py - A simple context stack for Gummworld2.
"""


cstack = []


def push(c, do_enter=True):
    if cstack:
        if __debug__: print "CONTEXT: suspending", cstack[-1].__class__.__name__
        cstack[-1].suspend()
    if __debug__: print "CONTEXT: pushing", c.__class__.__name__
    cstack.append(c)
    if do_enter:
        if __debug__: print "CONTEXT: enter", c.__class__.__name__
        c.enter()


def pop(n = 1):
    for j in range(n):
        if cstack:
            if __debug__: print "CONTEXT: pop/exit", cstack[-1].__class__.__name__
            c = cstack[-1]
            del cstack[-1]
            c.exit()
        if cstack:
            if __debug__: print "CONTEXT: resume", cstack[-1].__class__.__name__
            cstack[-1].resume()


def top():
    return cstack[-1] if cstack else None


class Context(object):
    def __init__(self):
        object.__init__(self)
    def update(self, dt):
        """Called once per frame"""
        pass
    def draw(self, dt):
        """Refresh the screen"""
        pass
    def suspend(self):
        """Called when another context is pushed on top of this one."""
        pass
    def resume(self):
        """Called when another context is popped off the top of this one."""
        pass
    def enter(self):
        """Called when this context is pushed onto the stack."""
        pass
    def exit(self):
        """Called when this context is popped off the stack."""
        pass
    push = staticmethod(push)
    pop = staticmethod(pop)
    top = staticmethod(top)
