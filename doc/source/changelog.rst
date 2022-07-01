.. _changelog:

ChangeLog
=========

This is a log of changes to ``ytree`` over its release history.

Contributors
------------

The `CREDITS file
<https://github.com/ytree-project/ytree/blob/main/CREDITS>`__
contains the most up-to-date list of everyone who has contributed to the
``ytree`` source code.

Version 3.1.2
-------------

Release date: *March 11, 2022*

Minor Enhancements
^^^^^^^^^^^^^^^^^^

 * Add always_do option to AnalysisPipeline operations.
   (`PR #129 <https://github.com/ytree-project/ytree/pull/129>`__)

Bugfixes
^^^^^^^^

 * Make sure to refresh vector analysis fields after setting values.
   (`PR #127 <https://github.com/ytree-project/ytree/pull/127>`__)

 * Fix analysis pipeline operation filtering.
   (`PR #129 <https://github.com/ytree-project/ytree/pull/129>`__)

 * Get filename from correct part of line in consistent-trees format.
   (`PR #131 <https://github.com/ytree-project/ytree/pull/131>`__)

Infrastructure Updates
^^^^^^^^^^^^^^^^^^^^^^

 * Officially support and start testing Python 3.10.
   (`PR #128 <https://github.com/ytree-project/ytree/pull/128>`__)

Version 3.1.1
-------------

Release date: *February 3, 2022*

Bugfixes
^^^^^^^^

 * Allow parallel_trees to work with non-root trees.
   (`PR #123 <https://github.com/ytree-project/ytree/pull/123>`__)

 * Use smarter regexes to get AHF naming scheme.
   (`PR #118 <https://github.com/ytree-project/ytree/pull/118>`__)

 * Add return value to comply with yt.
   (`PR #121 <https://github.com/ytree-project/ytree/pull/121>`__)

Infrastructure Updates
^^^^^^^^^^^^^^^^^^^^^^
 * Implement _apply_units method.
   (`PR #122 <https://github.com/ytree-project/ytree/pull/122>`__)

 * Enable parallelism on circleci.
   (`PR #120 <https://github.com/ytree-project/ytree/pull/120>`__)

 * Create pypi upload action.
   (`PR #124 <https://github.com/ytree-project/ytree/pull/124>`__)

Version 3.1
-----------

Release date: *August 30, 2021*

New Featues
^^^^^^^^^^^

 * Add AnalysisPipeline
   (`PR #113 <https://github.com/ytree-project/ytree/pull/113>`__)

 * Add Parallel Iterators
   (`PR #112 <https://github.com/ytree-project/ytree/pull/112>`__)

Version 3.0
-----------

Release date: *August 3, 2021*

New Featues
^^^^^^^^^^^

 * Halo selection and generation with yt data objects
   (`PR #82 <https://github.com/ytree-project/ytree/pull/82>`__)

 * Add frontends for consistent-trees hlist and locations.dat files
   (`PR #48 <https://github.com/ytree-project/ytree/pull/48>`__)

 * Add consistent-trees HDF5 frontend
   (`PR #53 <https://github.com/ytree-project/ytree/pull/53>`__)

 * Add LHaloTree_hdf5 frontend
   (`PR #81 <https://github.com/ytree-project/ytree/pull/81>`__)

 * Add TreeFrog frontend
   (PR `#103 <https://github.com/ytree-project/ytree/pull/103>`__,
   `#95 <https://github.com/ytree-project/ytree/pull/95>`__,
   `#88 <https://github.com/ytree-project/ytree/pull/88>`__)

 * Add Moria frontend
   (`PR #84 <https://github.com/ytree-project/ytree/pull/84>`__)

 * Add get_node and get_leaf_nodes functions
   (`PR #80 <https://github.com/ytree-project/ytree/pull/80>`__)

 * Add get_root_nodes function
   (`PR #91 <https://github.com/ytree-project/ytree/pull/91>`__)

 * Add add_vector_field function
   (`PR #71 <https://github.com/ytree-project/ytree/pull/71>`__)

 * Add plot customization
   (`PR #49 <https://github.com/ytree-project/ytree/pull/49>`__)

Enhancements
^^^^^^^^^^^^

 * All functions returning TreeNodes now return generators for a
   significant speed and memory usage improvement.
   (PR `#104 <https://github.com/ytree-project/ytree/pull/104>`__,
   `#64 <https://github.com/ytree-project/ytree/pull/64>`__,
   `#61 <https://github.com/ytree-project/ytree/pull/61>`__)

 * Speed and usability improvements to select_halos function
   (PR `#83 <https://github.com/ytree-project/ytree/pull/83>`__,
   `#72 <https://github.com/ytree-project/ytree/pull/72>`__)

 * Add parallel analysis docs
   (`PR #106 <https://github.com/ytree-project/ytree/pull/106>`__)

 * Make field_data an public facing attribute.
   (`PR #105 <https://github.com/ytree-project/ytree/pull/105>`__)

 * Improved sorting for node_io_loop in ctrees_group and ctrees_hdf5
   (`PR #87 <https://github.com/ytree-project/ytree/pull/87>`__)

 * Relax requirements on cosmological parameters and add load options
   for AHF frontend
   (`PR #76 <https://github.com/ytree-project/ytree/pull/76>`__)

 * Speed and usability updates to save_arbor function
   (PR `#68 <https://github.com/ytree-project/ytree/pull/68>`__,
   `#58 <https://github.com/ytree-project/ytree/pull/58>`__)

 * Various infrastructure updates for newer versions of Python and
   dependencies
   (PR `#92 <https://github.com/ytree-project/ytree/pull/92>`__,
   `#78 <https://github.com/ytree-project/ytree/pull/78>`__,
   `#75 <https://github.com/ytree-project/ytree/pull/75>`__,
   `#60 <https://github.com/ytree-project/ytree/pull/60>`__,
   `#54 <https://github.com/ytree-project/ytree/pull/54>`__,
   `#45 <https://github.com/ytree-project/ytree/pull/45>`__)

 * Update frontend development docs
   (`PR #69 <https://github.com/ytree-project/ytree/pull/69>`__)

 * CI updates
   (PR `#101 <https://github.com/ytree-project/ytree/pull/101>`__,
   `#96 <https://github.com/ytree-project/ytree/pull/96>`__,
   `#94 <https://github.com/ytree-project/ytree/pull/94>`__,
   `#93 <https://github.com/ytree-project/ytree/pull/93>`__,
   `#86 <https://github.com/ytree-project/ytree/pull/86>`__,
   `#79 <https://github.com/ytree-project/ytree/pull/79>`__,
   `#74 <https://github.com/ytree-project/ytree/pull/74>`__,
   `#73 <https://github.com/ytree-project/ytree/pull/73>`__)
   `#63 <https://github.com/ytree-project/ytree/pull/63>`__,
   `#55 <https://github.com/ytree-project/ytree/pull/55>`__,
   `#51 <https://github.com/ytree-project/ytree/pull/51>`__,
   `#50 <https://github.com/ytree-project/ytree/pull/50>`__,
   `#43 <https://github.com/ytree-project/ytree/pull/43>`__,
   `#42 <https://github.com/ytree-project/ytree/pull/42>`__)

 * Remove support for ytree-1.x outputs
   (`PR #62 <https://github.com/ytree-project/ytree/pull/62>`__)

 * Drop support for python 3.5
   (`PR #59 <https://github.com/ytree-project/ytree/pull/59>`__)

 * Drop support for Python 2
   (`PR #41 <https://github.com/ytree-project/ytree/pull/41>`__)

Bugfixes
^^^^^^^^

 * Use file sizes of loaded arbor when only saving analysis fields.
   (`PR #100 <https://github.com/ytree-project/ytree/pull/100>`__)

 * Use regex for more robust filename check.
   (PR `#77 <https://github.com/ytree-project/ytree/pull/77>`__,
   `#47 <https://github.com/ytree-project/ytree/pull/47>`__)

 * Fix issue with saving full arbor
   (`PR #70 <https://github.com/ytree-project/ytree/pull/70>`__)

 * Check if attr is bytes or string.
   (`PR #57 <https://github.com/ytree-project/ytree/pull/57>`__)

 * Fix arg in error message.
   (`PR #56 <https://github.com/ytree-project/ytree/pull/56>`__)

 * Account for empty ctrees files in data files list
   (`PR #52 <https://github.com/ytree-project/ytree/pull/52>`__)

Version 2.3
-----------

Release date: *December 17, 2019*

This release marks the `acceptance of the ytree paper
<https://github.com/openjournals/joss-reviews/issues/1881>`__ in
`JOSS <https://joss.theoj.org/>`__.

This is the last release to support Python 2.

New Features
^^^^^^^^^^^^

 * Add TreePlot for plotting and examples docs
   (`PR #39 <https://github.com/ytree-project/ytree/pull/39>`__)

Enhancements
^^^^^^^^^^^^

 * Add time field
   (`PR #25 <https://github.com/ytree-project/ytree/pull/25>`__)
 * Move treefarm module to separate package
   (`PR #28 <https://github.com/ytree-project/ytree/pull/28>`__)

Version 2.2.1
-------------

Release date: *October 24, 2018*

Enhancements
^^^^^^^^^^^^

 * Refactor of CatalogDataFile class
   (`PR #21 <https://github.com/ytree-project/ytree/pull/21>`__)
 * Simplify requirements file for docs build on readthedocs.io
   (`PR #22 <https://github.com/ytree-project/ytree/pull/22>`__)

Bugfixes
^^^^^^^^

 * Restore access to analysis fields for tree roots
   (`PR #23 <https://github.com/ytree-project/ytree/pull/23>`__)
 * fix field access on non-root nodes when tree is not setup
   (`PR #20 <https://github.com/ytree-project/ytree/pull/20>`__)
 * fix issue of uid and desc_uid fields being clobbered during
   initial field access
   (`PR #19 <https://github.com/ytree-project/ytree/pull/19>`__)

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
