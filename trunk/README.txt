WHAT'S IN THE DISTRIBUTION
==========================

data/
  The game resource directory. The data module knows how to look files up in here.

docs/
  * Gummworld2 HTML docs produced by pydoc.
  * A third_party/ subdirectory containing licenses and other readmes for third-party components included with Gummworld2.

examples/
  Demonstrations of some of what's possible with Gummworld2:
  * Scrolling maps
  * Tiled maps
  * Collapsing and reducing map layers to boost performance
  * The various world types
  * Quadtree exercisers
  * Geometry collisions
  * Views (subsurfaces)

gamelib/
  Subdirectories:
  * gummworld2/, the map scrolling library for use in games
  * pgu/gui/, a widget based GUI included for the world editor; you're free to use it, but it's not required for games

make_docs, pydoc
  The script used to create the HTML docs, and to start the pydoc viewer web service.

paths.py*
  Convenient module for run-time configuration of library path.

world_editor.py*
  The world editor. Make rects, circles, polygons overlaying a map; save 'em, load 'em in a game, use 'em as collidable objects.


USING GUMMWORLD2
================

See the docs/ directory of the distribution for the HTML version of library
docstrings. There is a convenience pydoc script in the base directory that can
be used to start a PyDoc server.

There are many simple examples in the examples/ directory.

See gamelib/gummworl2/toolkit.py for examples of how to work directly with classes
like Map, MapLayer, Camera, HUD, etc.

If that's not enough to get you rolling, drop by the discussion group to get some
personal help: https://groups.google.com/group/gummworld2


REQUESTING HELP AND IMPROVEMENTS
================================

Simple questions can be sent to stabbingfinger@gmail.com.

For deeper topics starting a discussion at
https://groups.google.com/group/gummworld2 would be appreciated. That way more
people could benefit from the exchange.

Enhancement requests and bug reports may be submitted at the project site
http://code.google.com/p/gummworld2/.
