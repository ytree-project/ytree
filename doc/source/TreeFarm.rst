.. _treefarm:

Making Merger-trees from Gadget FoF/Subfind
===========================================

The ytree TreeFarm can compute merger-trees either for all halos,
starting at the beginning of the simulation, or for specific halos,
starting at the final output and moving backward.  These two
use-cases are covered separately.  Halo catalogs must be in the form
created by the Gadget FoF halo finder or Subfind substructure
finder.

Computing a Full Merger-tree
----------------------------

TreeFarm accepts a ``yt`` time-series object over which the
merger-tree will be computed.

.. code-block:: python

   import yt
   import ytree

   ts = yt.DatasetSeries("data/groups_*/*.0.hdf5")
   my_tree = TreeFarm(ts)
   my_tree.trace_descendents("Group", filename="all_halos/")

This process will create a new halo catalogs with the additional
field representing the descendent ID for each halo.  These can
be loaded using ``yt`` like any other catalogs.  Once complete,
the final merger-tree can be loaded in following :ref:`these
instructions <load-treefarm>`.

Computing a Targeted Merger-tree
--------------------------------
