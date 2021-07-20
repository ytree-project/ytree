.. _arbor:

Working with Merger Trees
=========================

The :class:`~ytree.data_structures.arbor.Arbor` class is responsible for loading
and providing access to merger tree data. In this document, a loaded merger tree
dataset is referred to as an **arbor**. ``ytree`` provides several different
ways to navigate, query, and analyze merger trees. It is recommended that you
read this entire section to identify the way that is best for what you want to do.

Loading Data
------------

``ytree`` can load merger tree data from multiple sources using
the :func:`~ytree.data_structures.load.load` command.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("consistent_trees/tree_0_0_0.dat")

This command will determine the correct format and read in the data
accordingly. For examples of loading each format, see below.

.. toctree::
   :maxdepth: 2

   Loading

Getting Started with Merger Trees
---------------------------------

Very little happens immediately after a dataset has been loaded. All tree
construction and data access occurs only on demand. After loading,
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
``ytree`` supports accessing fields by their native names as well as generalized
aliases. For more information on fields in ``ytree``, see :ref:`fields`.

How many trees are there?
^^^^^^^^^^^^^^^^^^^^^^^^^

The total number of trees in the arbor can be found using the ``size``
attribute. As soon as any information about the collection of trees within the
loaded dataset is requested, arrays will be created containing the metadata
required for generating the root nodes of every tree.

.. code-block:: python

   >>> print (a.size)
   Loading tree roots: 100%|██████| 5105985/5105985 [00:00<00:00, 505656111.95it/s]
   327

Root Fields
^^^^^^^^^^^

Field data for all tree roots is accessed by querying the
:class:`~ytree.data_structures.arbor.Arbor` in a
dictionary-like manner.

.. code-block:: python

   >>> print (a["mass"])
   Getting root fields: 100%|██████████████████| 327/327 [00:00<00:00, 9108.67it/s]
   [  6.57410072e+14   5.28489209e+14   5.18129496e+14   4.88920863e+14, ...,
      8.68489209e+11   8.68489209e+11   8.68489209e+11] Msun

``ytree`` uses the `unyt <https://unyt.readthedocs.io/>`__ package for symbolic units
on NumPy arrays.

.. code-block:: python

   >>> print (a["virial_radius"].to("Mpc/h"))
   [ 1.583027  1.471894  1.462154  1.434253  1.354779  1.341322  1.28617, ...,
     0.173696  0.173696  0.173696  0.173696  0.173696] Mpc/h

When dealing with cosmological simulations, care must be taken to distinguish
between comoving and proper reference frames. Please read :ref:`frames` before
your magical ``ytree`` journey begins.

Accessing Individual Trees
^^^^^^^^^^^^^^^^^^^^^^^^^^

Individual trees can be accessed by indexing the
:class:`~ytree.data_structures.arbor.Arbor` object.

.. code-block:: python

   >>> print (a[0])
   TreeNode[12900]

A :class:`~ytree.data_structures.tree_node.TreeNode` is one halo in a merger tree.
The number is the universal identifier associated with halo. It is unique
to the whole arbor. Fields can be accessed for any given
:class:`~ytree.data_structures.tree_node.TreeNode` in the same dictionary-like
fashion.

.. code-block:: python

   >>> my_tree = a[0]
   >>> print (my_tree["mass"])
   657410071942446.1 Msun

Array slicing can also be used to select multiple
:class:`~ytree.data_structures.tree_node.TreeNode` objects. This will return a
generator that can be iterated over or cast to a list.

.. code-block:: python

   >>> every_second_tree = list(a[::2])
   >>> print (every_second_tree[0]["mass"])
   657410071942446.1 Msun

Note, the :class:`~ytree.data_structures.arbor.Arbor` object does not
store individual :class:`~ytree.data_structures.tree_node.TreeNode` objects, it
only generates them. Thus, one must explicitly keep around any
:class:`~ytree.data_structures.tree_node.TreeNode` object for changes to persist.
This is illustrated below:

.. code-block:: python

   >>> # this will not work
   >>> a[0].thing = 5
   >>> print (a[0].thing)
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
   AttributeError: 'TreeNode' object has no attribute 'thing'
   >>> # this will work
   >>> my_tree = a[0]
   >>> my_tree.thing = 5
   >>> print (my_tree.thing)
   5

The only exception to this is computing the number of nodes in a tree. This
information will be propagated back to the
:class:`~ytree.data_structures.arbor.Arbor` as it can be expensive to compute
for large trees.

.. code-block:: python

   >>> my_tree = a[0]
   print (my_tree.tree_size) # call function to calculate tree size
   691
   >>> new_tree = a[0]
   print (new_tree.tree_size) # retrieved from a cache
   691

Accessing the Nodes in a Tree or Forest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A node is defined as a single halo at a single time in a merger tree.
Throughout these docs, the words halo and node are used interchangeably.
Nodes in a given tree can be accessed in three different ways: by
:ref:`tree-access`, :ref:`forest-access`, or :ref:`progenitor-access`.
Each of these will return a generator of
:class:`~ytree.data_structures.tree_node.TreeNode` objects or field
values for all :class:`~ytree.data_structures.tree_node.TreeNode` objects
in the tree, forest, or progenitor line. To get a specific node from a
tree, see :ref:`single-node-access`.

.. note:: Access by forest is supported even for datasets that do not
   group trees by forest. If you have no requirement for the order in
   which nodes are to be returned, then access by forest is recommended
   as it will be considerably faster than access by tree. Access by tree
   is effectively a depth-first walk through the tree. This requires
   additional data structures to be built, whereas forest access does
   not.

.. _tree-access:

Accessing All Nodes in a Tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The full lineage of the tree can be accessed by querying any
:class:`~ytree.data_structures.tree_node.TreeNode` with the ``tree`` keyword.
As of ``ytree`` version 3.0, this returns a generator that can be used
to loop through all nodes in the tree.

.. code-block:: python

   >>> print (my_tree["tree"])
   <generator object TreeNode._tree_nodes at 0x11bbc1f20>
   >>> # loop over nodes
   >>> for my_node in my_tree["tree"]:
   ...     print (my_node, my_node["mass"])
   TreeNode[12900] 657410100000000.0 Msun
   TreeNode[12539] 657410100000000.0 Msun
   TreeNode[12166] 653956900000000.0 Msun
   TreeNode[11796] 650071960000000.0 Msun
   ...

To store all the nodes in a single structure, convert it to a list:

   >>> print (list(my_tree["tree"]))
   [TreeNode[12900], TreeNode[12539], TreeNode[12166], TreeNode[11796], ...
    TreeNode[591]]

Fields can be queried for the tree by including the field name.

.. code-block:: python

   >>> print (my_tree["tree", "virial_radius"])
   [ 2277.73669065  2290.65899281  2301.43165468  2311.47625899  2313.99280576 ...
     434.59856115   410.13381295   411.25755396] kpc

The above examples will work for any halo in the tree, not just the final halo.
The full tree leading up to any given halo can be accessed in the same way.

.. code-block:: python

   >>> tree_nodes = list(my_tree["tree"])
   >>> # start with the 3rd halo in the above tree
   >>> sub_tree = tree_nodes[2]
   >>> print (list(sub_tree["tree"]))
   [TreeNode[12166], TreeNode[11796], TreeNode[11431], TreeNode[11077], ...
    TreeNode[591]]
   >>> print (sub_tree["tree", "virial_radius"])
   [2301.4316  2311.4763  2313.993   2331.413   2345.5454  2349.918 ...
    434.59857  410.13382  411.25757] kpc

.. _forest-access:

Accessing All Nodes in a Forest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :ref:`load-ctrees-hdf5`, :ref:`load-lhalotree`, :ref:`load-lhalotree-hdf5`,
:ref:`load-moria`, :ref:`load-treefrog` formats provide access to halos grouped
by forest. A forest is a group of trees with halos that interact in a non-merging
way through processes like fly-bys.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("consistent_trees_hdf5/soa/forest.h5",
   ...                access="forest")
   >>> my_forest = a[0]
   >>> # all halos in the forest
   >>> print (list(my_forest["forest"]))
   [TreeNode[90049568], TreeNode[88202573], TreeNode[86292249], ...
    TreeNode[9272027], TreeNode[7435733], TreeNode[5768880]]
   >>> # all halo masses in forest
   >>> print (my_forest["forest", "mass"])
   [3.38352524e+11 3.34071450e+11 3.34071450e+11 3.31709477e+11 ...
    7.24092117e+09 4.34455270e+09] Msun

To find all the roots in that forest, i.e., the roots of all individual trees
contained, see :ref:`getting_root_nodes`.

Accessing a Halo's Ancestors and Descendent
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The direct ancestors of any
:class:`~ytree.data_structures.tree_node.TreeNode` object can be accessed
through the ``ancestors`` attribute.

.. code-block:: python

   >>> my_ancestors = list(my_tree.ancestors)
   >>> print (my_ancestors)
   [TreeNode[12539]]

A halo's descendent can be accessed in a similar fashion.

.. code-block:: python

   >>> print (my_ancestors[0].descendent)
   TreeNode[12900]

.. _progenitor-access:

Accessing the Progenitor Lineage of a Tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Similar to the ``tree`` keyword, the ``prog`` keyword can be used to access
the line of main progenitors. Just as above, this returns a generator
of :class:`~ytree.data_structures.tree_node.TreeNode` objects.

.. code-block:: python

   >>> print (list(my_tree["prog"]))
   [TreeNode[12900], TreeNode[12539], TreeNode[12166], TreeNode[11796], ...
    TreeNode[62]]

Fields for the main progenitors can be accessed just like for the whole
tree.

.. code-block:: python

   >>> print (my_tree["prog", "mass"])
   [  6.57410072e+14   6.57410072e+14   6.53956835e+14   6.50071942e+14 ...
      8.29496403e+13   7.72949640e+13   6.81726619e+13   5.99280576e+13] Msun

Progenitor lists and fields can be accessed for any halo in the tree.

.. code-block:: python

   >>> tree_nodes = list(my_tree["tree"])
   >>> # pick a random halo in the tree
   >>> my_halo = tree_nodes[42]
   >>> print (list(my_halo["prog"]))
   [TreeNode[588], TreeNode[446], TreeNode[317], TreeNode[200], TreeNode[105],
    TreeNode[62]]
   >>> print (my_halo["prog", "virial_radius"])
   [1404.1354 1381.4087 1392.2404 1363.2145 1310.3842 1258.0159] kpc

Customizing the Progenitor Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the progenitor line is defined as the line of the most
massive ancestors. This can be changed by calling the
:func:`~ytree.data_structures.arbor.Arbor.set_selector`.

.. code-block:: python

   >>> a.set_selector("max_field_value", "virial_radius")

New selector functions can also be supplied. These functions should
minimally accept a list of ancestors and return a single
:class:`~ytree.data_structures.tree_node.TreeNode`.

.. code-block:: python

   >>> def max_value(ancestors, field):
   ...     vals = np.array([a[field] for a in ancestors])
   ...     return ancestors[np.argmax(vals)]
   ...
   >>> ytree.add_tree_node_selector("max_field_value", max_value)
   >>>
   >>> a.set_selector("max_field_value", "mass")
   >>> my_tree = a[0]
   >>> print (list(my_tree["prog"]))

.. _single-node-access:

Accessing a Single Node in a Tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :func:`~ytree.data_structures.tree_node.TreeNode.get_node` functions can be
used to retrieve a single node from the forest, tree, or progenitor lists.

.. code-block:: python

   >>> my_tree = a[0]
   >>> my_node = my_tree.get_node("forest", 5)

This function can be called for any node in a tree. For selection by "tree" or
"prog", the index of the node returned will be relative to the calling node,
i.e., calling with 0 will return the original node. For selection by "forest",
the index is the absolute index within the entire forest and not relative to
the calling node.

Accessing the Leaf Nodes of a Tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The leaf nodes of a tree are the nodes with no ancestors. These are the very first
halos to form. Accessing them for any tree can be useful for semi-analytical
models or any framework where you want to start at the origins of a halo and work
forward in time. The :func:`~ytree.data_structures.tree_node.TreeNode.get_leaf_nodes`
function will return a generator of all leaf nodes of a tree's forest, tree, or
progenitor lists.

.. code-block:: python

   >>> my_tree = a[0]
   >>> my_leaves = my_tree.get_leaf_nodes(selector="forest")
   >>> for my_leaf in my_leaves:
   ...     print (my_leaf)

Similar to the :func:`~ytree.data_structures.tree_node.TreeNode.get_node`
function, calling :func:`~ytree.data_structures.tree_node.TreeNode.get_leaf_nodes`
with ``selector`` set to "tree" or "prog" will return only leaf nodes from the
tree for which the calling node is the head. With ``selector`` set to "forest",
the resulting leaf nodes will be all the leaf nodes in the forest, regardless of
the calling node.

.. _getting_root_nodes:

Accessing the Root Nodes of a Forest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A forest can have multiple root nodes, i.e., nodes that have no descendent. The
:func:`~ytree.data_structures.tree_node.TreeNode.get_root_nodes` function will
return a generator of all the root nodes in the forest. This function can be called
from any tree within a forest.

.. code-block:: python

   >>> my_tree = a[0]
   >>> my_roots = my_tree.get_root_nodes()
   >>> for my_root in my_roots:
   ...     print (my_root)

.. _saving-trees:

Saving Arbors and Trees
-----------------------

``Arbors`` of any type can be saved to a universal file format with the
:func:`~ytree.data_structures.arbor.Arbor.save_arbor` function. These can be
reloaded with the :func:`~ytree.data_structures.load.load` command. This
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
:func:`~ytree.data_structures.tree_node.TreeNode.save_tree`.

.. code-block:: python

   >>> my_tree = a[0]
   >>> fn = my_tree.save_tree()
   Creating field arrays [1/1]: 100%|████| 4897/4897 [00:00<00:00, 13711286.17it/s]
   >>> a2 = ytree.load(fn)

Searching Through Merger Trees (Accessing Like a Database)
----------------------------------------------------------

There are a couple different ways to search through a merger tree dataset to find
halos meeting various criteria, similar to the type of selection done with a
relational database. The method discussed in :ref:`select-halos` can be used with
all data loadable with ``ytree``, while the one described in :ref:`select-halos-yt`
is only available for :ref:`load-ytree`.

.. _select-halos:

Select Halos
^^^^^^^^^^^^

The :func:`~ytree.data_structures.arbor.Arbor.select_halos` function can be used to
search the :class:`~ytree.data_structures.arbor.Arbor` for halos matching a specific
set of criteria.

.. code-block:: python

   >>> halos = list(a.select_halos("tree['forest', 'mass'].to('Msun') > 5e11"))
   Selecting halos (found 3): 100%|███████████████| 32/32 [00:00<00:00, 107.70it/s]
   >>> print (halos)
   [TreeNode[1457223360], TreeNode[1457381406], TreeNode[1420495006]]

The :func:`~ytree.data_structures.arbor.Arbor.select_halos` function will return a
generator of :class:`~ytree.data_structures.tree_node.TreeNode` objects that can be
iterated over or cast to a list, as above. The function will return halos as they
are found so the user does not have to wait until the end to begin working with
them. The progress bar will continually update to report the number of matches
found.

The selection criteria string should be designed to ``eval`` correctly
with a :class:`~ytree.data_structures.tree_node.TreeNode` object, named
"tree". More complex criteria can be supplied using \& and \|.

.. code-block:: python

   >>> for halo in a.select_halos("(tree['tree', 'mass'].to('Msun') > 2e11) & (tree['tree', 'redshift'] < 0.2)"):
   ...     progenitor_pos = halo["prog", "position"]
   Selecting halos (found 69): 100%|███████████████| 32/32 [00:01<00:00, 22.50it/s]

.. _select-halos-yt:

Select Halos with yt
^^^^^^^^^^^^^^^^^^^^

.. note:: This functionality only works with :ref:`load-ytree`. You will need to
   :ref:`save your data in the ytree format <saving-trees>`.

The :func:`~ytree.frontends.ytree.arbor.YTreeArbor.get_yt_selection` function
provides enhanced functionality beyond the capabilities of
:func:`~ytree.data_structures.arbor.Arbor.select_halos` by loading the dataset
into `yt <https://yt-project.org/>`__. Given search criteria,
:func:`~ytree.frontends.ytree.arbor.YTreeArbor.get_yt_selection` will return a
:class:`~yt.data_objects.selection_objects.cut_region.YTCutRegion` data container
that can then be queried to get the value of any field for all halos meeting the
criteria. This :class:`~yt.data_objects.selection_objects.cut_region.YTCutRegion`
can then be used to :ref:`generate tree nodes <halos-from-selection>` or
:ref:`query fields <yt-data-containers>`.

Creating the Selection
^^^^^^^^^^^^^^^^^^^^^^

Search criteria can be provided using a series of keywords: ``above``, ``below``,
``equal``, and ``about``.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("arbor/arbor.h5")
   >>> selection = a.get_yt_selection(,
   ...     above=[("mass", 1e13, "Msun"),
   ...            ("redshift", 0.5)])

An individual criterion should be expressed as a tuple
(e.g., ``(field, value, <units>)``), and the above keywords accept a list of those
tuples. The criteria keywords can be given together and the halos must meet all
criteria, i.e., the criteria are combined with an AND operator.

.. code-block:: python

   >>> selection = a.get_yt_selection(
   ...     below=[("mass", 1e13, "Msun")],
   ...     above=[("redshift", 1)])

For more complex search criteria, a cut region conditional string can be
provided instead. These should be of the form described in :ref:`cut-regions`.
These cannot not be given with any of the previously mentioned keywords.

.. code-block:: python

    >>> selection = a.get_yt_selection(
    ...     conditionals=['obj["halos", "mass"] > 1e12'])

Querying the Selection
^^^^^^^^^^^^^^^^^^^^^^

The selection object returned by
:func:`~ytree.frontends.ytree.arbor.YTreeArbor.get_yt_selection` can then be
queried to get field values for all matching halos. Fields should be queried
as ``("halos", <field name>)``.

.. code-block:: python

   >>> # halos with masses of 1e14 Msun +/- 5%
   >>> selection = a.get_yt_selection(
           about=[("mass", 1e14, "Msun", 0.05)])

   >>> print (selection["halos", "redshift"])
   [0.82939091 0.97172537 1.02453741 0.31893065 0.74571856 0.97172537 ...
    0.50455122 0.53499009 0.18907477 0.29567248 0.31893065] dimensionless

.. _halos-from-selection:

Getting Halos from the Selection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :func:`~ytree.frontends.ytree.arbor.YTreeArbor.get_nodes_from_selection`
function will return a generator of
:class:`~ytree.data_structures.tree_node.TreeNode` objects for all halos
contained within the selection.

.. code-block:: python

   >>> # halos with masses of 1e14 Msun +/- 5%
   >>> selection = a.get_yt_selection(
           about=[("mass", 1e14, "Msun", 0.05)])

   >>> for node in a.get_nodes_from_selection(selector):
   ...     print (node["prog", "mass"])

This function can generate :class:`~ytree.data_structures.tree_node.TreeNode`
objects for :ref:`any yt data container <yt-data-containers>`.

.. _yt-data-containers:

Halos and Fields from yt Data Containers
----------------------------------------

.. note:: This functionality only works with :ref:`load-ytree`. You will need to
   :ref:`save your data in the ytree format <saving-trees>`.

For merger tree data in the :ref:`ytree format <load-ytree>`, the
:attr:`~ytree.frontends.ytree.arbor.YTreeArbor.ytds` attribute provides access
to the data as a `yt <https://yt-project.org/>`__ dataset. This allows one to
analyze the entire dataset using the full range of functionality provided by
``yt``. In this way, a merger tree dataset is very much like any particle dataset,
where each particle represent a halo at a single time. For example, this makes it
possible to select halos within :ref:`geometric data containers <data-objects>`,
like spheres or regions.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("arbor/arbor.h5")

   >>> ds = a.ytds
   >>> sphere = ds.sphere(ds.domain_center, (5, "Mpc"))
   >>> print (sphere["halos", "mass"])

These data containers can then be given to the
:func:`~ytree.frontends.ytree.arbor.YTreeArbor.get_nodes_from_selection` function to
:ref:`get the tree nodes <halos-from-selection>` for all halos within the
container.

.. code-block:: python

   >>> sphere = ds.sphere(ds.domain_center, (5, "Mpc"))
   >>> for node in a.get_nodes_from_selection(sphere):
   ...     print (node["position"])
