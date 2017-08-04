.. _loading:

Loading Data
============

Below are instructions for loading all supported datasets.

Consistent-Trees
----------------

The `consistent-trees <https://bitbucket.org/pbehroozi/consistent-trees>`_
format is typically one or a few files with a naming convention like
"tree_0_0_0.dat".  To load these files, just give the filename

.. code-block:: python

   import ytree
   a = ytree.load("consistent_trees/tree_0_0_0.dat")

Rockstar Catalogs
-----------------

Rockstar catalogs with the naming convention "out_*.list" will contain
information on the descendent ID of each halo and can be loaded
independently of consistent-trees.  This can be useful when your
simulation has very few halos, such as in a zoom-in simulation.  To
load in this format, simply provide the path to one of these files.

.. code-block:: python

   import ytree
   a = ytree.load("rockstar/rockstar_halos/out_0.list")

.. _load-treefarm:

TreeFarm
--------

Merger-trees created with :ref:`TreeFarm <treefarm>` (ytree's merger-tree 
code for Gadget FoF/SUBFIND catalogs) can be loaded in by providing the
path to one of the catalogs created during the calculation.

.. code-block:: python

   import ytree
   a = ytree.load("tree_farm/tree_farm_descendents/fof_subhalo_tab_000.0.h5")

.. _load-ytree:

Saved Arbors
------------

Once merger-tree data has been loaded, it can be saved to a
universal format using :func:`~ytree.arbor.arbor.Arbor.save_arbor` or
:func:`~ytree.arbor.tree_node.TreeNode.save_tree`.  These can be loaded by
providing the path to the primary hdf5 file.

.. code-block:: python

   import ytree
   a = ytree.load("arbor/arbor.h5")

.. _load-old-arbor:

Saved Arbors from ytree 1.1
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Arbors created with version 1.1 of ytree and earlier can be reloaded by
providing the single file created.  It is recommended that arbors be
re-saved into the newer format as this will significantly improve
performance.

.. code-block:: python

   import ytree
   a = ytree.load("arbor.h5")
