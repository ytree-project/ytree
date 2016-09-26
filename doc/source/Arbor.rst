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

.. _load-arbor:

Arbor
^^^^^

Once merger-tree data has been loaded, it can be saved to a
universal format.  This can be loaded by providing the file created.

.. code-block:: python

   import ytree
   a = ytree.load("arbor.h5")

Working with Merger-trees
-------------------------

Once merger-tree data has been loaded into an ``Arbor``, the individual
trees will be stored in a list in the ``trees`` attribute.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("tree_0_0_0.dat")
   yt : [INFO     ] 2016-09-26 15:35:57,279 Loading tree data from tree_0_0_0.dat.
   Loading trees: 100%|████████████████████████| 327/327 [00:00<00:00, 4602.07it/s]
   yt : [INFO     ] 2016-09-26 15:35:57,666 Arbor contains 327 trees with 10405 total nodes.
   >>> print (len(a.trees))
   327
   >>> print (a.trees[0])
   TreeNode[0,0]

A ``TreeNode`` is one halo in a merger-tree.  The numbers correspond to the
halo ID and the level in the tree.  Like with ``yt`` data containers, fields
can be queried in dictionary fashion.

.. code-block:: python

   >>> my_tree = a.trees[0]
   >>> print (my_tree["mvir"])
   1.147e+13 Msun/h
   >>> print (my_tree["redshift"])
   0.0
   >>> print (my_tree["position"])
   [ 69.95449  60.33949  50.64586] Mpc/h
   >>> print (my_tree["velocity"])
   [ -789.51  1089.31  1089.31] km/s

A halo's ancestors are stored as a list in the ``ancestors`` attribute.

.. code-block:: python

   >>> print my_tree.ancestors
   [TreeNode[1,0]]

Iterating over a Tree
^^^^^^^^^^^^^^^^^^^^^

The ``twalk`` function provides an iterator that allows you to loop over
all halos in the tree.  This will iterate over all ancestors in a recursive
fashion.

.. code-block:: python

   >>> for my_node in my_tree.twalk():
   ...     print (my_node)


Accessing the Trunk of the Tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``line`` function allows one to query fields for the main trunk of the
tree.  By default, the "main trunk" follows the most massive progenitor.

.. code-block:: python

   >>> print my_tree.line("mvir")
   [  1.14700000e+13   1.20700000e+13   1.23700000e+13   1.23700000e+13, ...,
      6.64000000e+12   5.13100000e+12   3.32000000e+12   1.20700000e+12
      2.71600000e+12] Msun/h

The selection method used by the ``line`` function can be changed by calling
the ``set_selector`` function on the ``Arbor``.  For information on creating
new selection methods, see the example,
`~tree.tree_node_selector.max_field_value`.

.. code-block:: python

   >>> a.set_selector("min_field_value", "mvir")

Similar to ``twalk``, the ``lwalk`` function provide an iterator over the
trunk of a tree.

.. code-block:: python

   >>> for my_node in my_tree.lwalk():
   ...     print (my_node)

Similar to the ``line`` function, the ``tree`` function provides field
access to the whole tree.  However, since this is for all ancestors,
note that these are not necessarily in chronological order.

.. code-block:: python

   >>> print my_tree.tree("mvir")

Saving Arbors and Trees
-----------------------

``Arbors`` of any type can be saved to a universal file format which
can be reloaded in the :ref:`same way <load-arbor>`.

.. code-block:: python

   >>> a.save_arbor("my_arbor.h5")
   yt : [INFO     ] 2016-09-26 16:45:40,064 Saving field data to yt dataset: my_arbor.h5.
   >>> a2 = ytree.load("my_arbor.h5")
   Loading trees: 100%|████████████████████████| 327/327 [00:00<00:00, 1086.22it/s]
   yt : [INFO     ] 2016-09-26 16:46:26,383 Arbor contains 327 trees with 10405 total nodes.

Individual trees can be saved and reloaded in the same manner.

.. code-block:: python

   >>> fn = my_tree.save_tree()
   yt : [INFO     ] 2016-09-26 16:47:09,931 Saving field data to yt dataset: tree_0_0.h5.
   >>> atree = ytree.load(fn)
   Loading trees: 100%|█████████████████████████████| 1/1 [00:00<00:00, 669.38it/s]
   yt : [INFO     ] 2016-09-26 16:47:32,441 Arbor contains 1 trees with 45 total nodes.
