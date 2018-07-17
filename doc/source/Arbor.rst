.. _arbor:

Working with Merger-Trees
=========================

The :class:`~ytree.arbor.arbor.Arbor` class is responsible for loading
and providing access to merger-tree data.  Below, we demonstrate how
to load data and what can be done with it.

Loading Merger-Tree Data
------------------------

ytree can load merger-tree data from multiple sources using
the :func:`~ytree.arbor.load` command.

.. code-block:: python

   import ytree
   a = ytree.load("consistent_trees/tree_0_0_0.dat")

This command will determine the correct format and read in the data
accordingly.  For examples of loading each format, see below.

.. toctree::
   :maxdepth: 2

   Loading

Working with Merger-Tree Data
-----------------------------

Very little happens immediately after a dataset has been loaded.  All tree
construction and data access occurs only on demand.  After loading,
information such as the simulation box size, cosmological parameters, and
the available fields can be accessed.

.. code-block:: python

   >>> print (a.box_size)
   100.0 Mpc/h
   >>> print (a.hubble_constant, a.omega_matter, a.omega_lambda)
   0.695 0.285 0.715
   >>> print (a.field_list)
   ['scale', 'id', 'desc_scale', 'desc_id', 'num_prog', ...]

Similar to `yt <http://yt-project.org/docs/dev/analyzing/fields.html>`__,
ytree supports accessing fields by their native names as well as generalized
aliases.  For more information on fields in ytree, see :ref:`fields`.

How many trees are there?
^^^^^^^^^^^^^^^^^^^^^^^^^

As soon as any information about the collection of trees within the loaded
dataset is requested, an array will be constructed containing objects
representing the root of each tree, i.e., the last descendent halo.  This
structure is accessed by querying the loaded ``Arbor`` directly.  It can
also be accessed as ``a.trees``.

.. code-block:: python

   >>> print (a.size)
   Loading tree roots: 100%|██████| 5105985/5105985 [00:00<00:00, 505656111.95it/s]
   327

Root Fields
^^^^^^^^^^^

Field data for all tree roots is accessed by querying the ``Arbor`` in a
dictionary-like manner.


.. code-block:: python

   >>> print (a["mass"])
   Getting root fields: 100%|██████████████████| 327/327 [00:00<00:00, 9108.67it/s]
   [  6.57410072e+14   5.28489209e+14   5.18129496e+14   4.88920863e+14, ...,
      8.68489209e+11   8.68489209e+11   8.68489209e+11] Msun

ytree uses `yt's system for symbolic units
<http://yt-project.org/docs/dev/analyzing/units/index.html>`__, allowing for simple
unit conversion.

.. code-block:: python

   >>> print (a["virial_radius"].to("Mpc/h"))
   [ 1.583027  1.471894  1.462154  1.434253  1.354779  1.341322  1.28617, ...,
     0.173696  0.173696  0.173696  0.173696  0.173696] Mpc/h

When dealing with cosmological simulations, care must be taken to distinguish
between comoving and proper reference frames.  Please read :ref:`frames` before
your magical ytree journey begins.

Accessing Individual Trees
^^^^^^^^^^^^^^^^^^^^^^^^^^

Individual trees can be accessed by indexing the ``Arbor`` object.

.. code-block:: python

   >>> print (a[0])
   TreeNode[12900]

A :class:`~ytree.arbor.tree_node.TreeNode` is one halo in a merger-tree.
The number is the universal identifier associated with halo.  It is unique
to the whole arbor.  Fields can be accessed for any given ``TreeNode`` in
the same dictionary-like fashion.

.. code-block:: python

   >>> print (a[0]["mass"])
   657410071942446.1 Msun

The full lineage of the tree can be accessed by querying any ``TreeNode``
with the `tree` keyword.

.. code-block:: python

   >>> my_tree = a[0]
   >>> print (my_tree["tree"])
   [TreeNode[12900] TreeNode[12539] TreeNode[12166] TreeNode[11796] ...
    TreeNode[591]]

Fields can be queried for the tree by including the field name.

.. code-block:: python

   >>> print (my_tree["tree", "virial_radius"])
   [ 2277.73669065  2290.65899281  2301.43165468  2311.47625899  2313.99280576 ...
     434.59856115   410.13381295   411.25755396] kpc

A halo's ancestors are stored as a list in the ``ancestors`` attribute.
The descendents are stored in a similar fashion.

.. code-block:: python

   >>> print (my_tree.ancestors)
   [TreeNode[12539]]
   >>> print (my_tree.ancestors[0].descendent)
   TreeNode[12900]

Accessing the Progenitor Lineage of a Tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Similar to the `tree` keyword, the `prog` keyword can be used to access
the line of main progenitors.

.. code-block:: python

   >>> print (my_tree["prog"])
   [TreeNode[12900] TreeNode[12539] TreeNode[12166] TreeNode[11796] ...
    TreeNode[62]]
   >>> print (my_tree["prog", "mass"])
   [  6.57410072e+14   6.57410072e+14   6.53956835e+14   6.50071942e+14 ...
      8.29496403e+13   7.72949640e+13   6.81726619e+13   5.99280576e+13] Msun

Customizing the Progenitor Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the progenitor line is defined as the line of the most
massive ancestors.  This can be changed by  calling the
:func:`~ytree.arbor.arbor.Arbor.set_selector`.

.. code-block:: python

   >>> a.set_selector("max_field_value", "virial_radius")

New selector functions can also be supplied.  These functions should
minimally accept a list of ancestors and return a single ``TreeNode``.

.. code-block:: python

   >>> def max_value(ancestors, field):
   ...     vals = np.array([a[field] for a in ancestors])
   ...     return ancestors[np.argmax(vals)]
   ...
   >>> ytree.add_tree_node_selector("max_field_value", max_value)
   >>>
   >>> a.set_selector("max_field_value", "mass")
   >>> print (a[0]["prog"])

Searching for Halos
-------------------

The :func:`~ytree.arbor.arbor.Arbor.select_halos` function can be used to
search the ``Arbor`` for halos matching a specific set of criteria.
This is similar to the type of selection done with a relational database.

.. code-block:: python

   >>> halos = a.select_halos('tree["tree", "redshift"] > 1',
   ...                        fields=["redshift"])
   >>> print (halos)
   [TreeNode[8987], TreeNode[6713], TreeNode[6091], TreeNode[448], ...,
    TreeNode[9683], TreeNode[8316], TreeNode[10788]]

The selection criteria string should be designed to ``eval`` correctly
with a ``TreeNode`` object named, "tree".  The ``fields`` keyword can
be used to specify a list of fields to preload for speeding up selection.

Saving Arbors and Trees
-----------------------

``Arbors`` of any type can be saved to a universal file format with the
:func:`~ytree.arbor.arbor.Arbor.save_arbor` function.  These can be
reloaded with the :func:`~ytree.arbor.arbor.load` command.  This
format is optimized for fast tree-building and field-access and so is
recommended for most situations.

.. code-block:: python

   >>> fn = a.save_arbor()
   Setting up trees: 100%|███████████████████| 327/327 [00:00<00:00, 483787.45it/s]
   Getting fields [1/1]: 100%|████████████████| 327/327 [00:00<00:00, 36704.51it/s]
   Creating field arrays [1/1]: 100%|█| 613895/613895 [00:00<00:00, 7931878.47it/s]
   >>> a2 = ytree.load(fn)

By default, all trees and all fields will be saved, but this can be
customized with the ``trees`` and ``fields`` keywords.

For convenience, individual trees can also be saved by calling
:func:`~ytree.arbor.tree_node.TreeNode.save_tree`.

.. code-block:: python

   >>> fn = a[0].save_tree()
   Creating field arrays [1/1]: 100%|████| 4897/4897 [00:00<00:00, 13711286.17it/s]
   >>> a2 = ytree.load(fn)

.. _frames:

An Important Note on Comoving and Proper Units
==============================================

Users of ``yt`` are likely familiar with conversion from proper to comoving
reference frames by adding "cm" to a unit.  For example, proper "Mpc"
becomes comoving with "Mpccm".  This conversion relies on all the data
being associated with a single redshift.  This is not possible here
because the dataset has values for multiple redshifts.  To account for
this, the proper and comoving unit systems are set to be equal to each
other.

.. code-block:: python

   >>> print (a.box_size)
   100.0 Mpc/h
   >>> print (a.box_size.to("Mpccm/h"))
   100.0 Mpccm/h

Data should be assumed to be in the reference frame in which it
was saved.  For length scales, this is typically the comoving frame.
When in doubt, the safest unit to use for lengths is "unitary", which
a system normalized to the box size.

.. code-block:: python

   >>> print (a.box_size.to("unitary"))
   1.0 unitary
