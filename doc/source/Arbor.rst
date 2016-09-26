.. _arbor:

Loading, Using, and Saving Merger-trees
=======================================

The ``Arbor`` class is responsible for loading and providing access
to merger-tree data.  Below, we discuss how to load in data and what
one can do with it.

Loading Merger-tree data
------------------------

``ytree`` can load merger-tree data from multiple sources using
the `~ytree.arbor.load` command.  This command will guess the correct
format and read in the data appropriately.  For examples of loading
each format, see below.

Consistent Trees
^^^^^^^^^^^^^^^^

The `consistent-trees <https://bitbucket.org/pbehroozi/consistent-trees>`_
format is typically one or a few files with a naming convention like
"tree_0_0_0.dat".  To load these files, just give the filename

.. code-block:: python

   import ytree
   a = ytree.load("tree_0_0_0.dat")

Rockstar Catalogs
^^^^^^^^^^^^^^^^^

Rockstar catalogs with the naming convention "out_*.list" will contain
information on the descendent ID of each halo and can be loaded
independently of consistent-trees.  This can be useful when your
simulation has very few halos, such as in a zoom-in simulation.  To
load in this format, simply provide the path to one of these files.

.. code-block:: python

   import ytree
   a = ytree.load("rockstar_halos/out_0.list")

.. _load-treefarm:

TreeFarm
^^^^^^^^

Merger-trees created with the :ref:`TreeFarm <treefarm>` method can
be loaded in by providing the path to one of the catalogs created
during the calculation.

.. code-block:: python

   import ytree
   a = ytree.load("all_halos/fof_subhalo_tab_016.0.hdf5.0.h5")

Arbor
^^^^^

Once merger-tree data has been loaded, it can be saved to a
universal format.  This can be loaded by providing the file created.

.. code-block:: python

   import ytree
   a = ytree.load("arbor.h5")
