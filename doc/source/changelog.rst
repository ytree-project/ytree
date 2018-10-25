.. _changelog:

ChangeLog
=========

This is a log of changes to ytree over its release history.

Contributors
------------

The `CREDITS file
<https://github.com/brittonsmith/ytree/blob/master/CREDITS>`__
contains the most up-to-date list of everyone who has contributed to the
ytree source code.

Version 2.2
-----------

Release date: *August 28, 2018*

New Features
^^^^^^^^^^^^

 * add vector fields.
 * add select_halos function.

Enhancements
^^^^^^^^^^^^

 * significant refactor of field and i/o systems.
 * upgrades to testing infrastructure.

Version 2.1.1
-------------

Release date: *April 23, 2018*

Bugfixes
^^^^^^^^

 * update environment.yml to fix broken readthedocs build.

Version 2.1
-----------

Release date: *April 20, 2018*

New Features
^^^^^^^^^^^^

 * add support for LHaloTree format.
 * add support for Amiga Halo Finder format.

Version 2.0.2
-------------

Release date: *February 16, 2018*

Enhancements
^^^^^^^^^^^^

 * significantly improved i/o for ytree frontend.

Version 2.0
-----------

Release date: *August 07, 2017*

This is significant overhaul of the ytree machinery.

New Features
^^^^^^^^^^^^

 * tree building and field i/o now occur on-demand.
 * support for yt-like derived fields that can be defined with simple
   functions.
 * support for yt-like alias fields allowing for universal
   field naming conventions to simplify writing scripts for multiple
   data formats.
 * support for analysis fields which allow users to save the results
   of expensive halo analysis to fields associated with each halo.
 * all fields in consistent-trees and Rockstar now fully supported with
   units.
 * an optimized format for saving and reloading trees for fast field access.

Enhancements
^^^^^^^^^^^^

 * significantly improved documentation including a guide to adding support
   for new file formats.

Version 1.1
-----------

Release date: *January 12, 2017*

New Features
^^^^^^^^^^^^

 * New, more yt-like field querying syntax for both arbors and tree
   nodes.

Enhancements
^^^^^^^^^^^^

 * Python3 now supported.
 * More robust unit system with restoring of unit registries from stored
   json.
 * Added minimum radius to halo sphere selector.
 * Replaced import of yt for specific imports of all required functions.
 * Added ytree logger.
 * Docs updated and API reference docs added.

Bugfixes
^^^^^^^^

 * Allow non-root trees to be saved and reloaded.
 * Fix bug allowing trees that end before the final output.

Version 1.0
-----------

Release date: *Sep 26, 2016*

The inaugural release of ytree!
