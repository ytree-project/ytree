.. _ytree_parallel:

Parallel Computing with ytree
=============================

``ytree`` provides functions for iterating over trees and nodes in
parallel. Underneath, they make use of the
:func:`~yt.utilities.parallel_tools.parallel_analysis_interface.parallel_objects`
function in ``yt``. This functionality is built on `MPI
<https://en.wikipedia.org/wiki/Message_Passing_Interface>`__, so it
can be used to parallelize analysis across multiple nodes of a
distributed computing system.

.. note:: Before reading this section, consult the
   :ref:`parallel-computation` section of the ``yt`` documentation to
   learn how to configure ``yt`` for running in parallel.

Enabling Parallelism and Running in Parallel
--------------------------------------------

All parallel computation in ``yt`` (and hence, ``ytree``) begins by
importing ``yt`` and calling the
:func:`~yt.utilities.parallel_tools.parallel_analysis_interface.enable_parallelism`
function.

.. code-block:: python

   import yt
   yt.enable_parallelism()
   import ytree

In all cases, scripts must be run with ``mpirun`` to work in
parallel. For example, to run on 4 processors, do:

.. code-block:: bash

   $ mpirun -np 4 python my_analysis.py

where "my_analysis.py" is the name of the script.

.. _parallel_iterators:

Parallel Iterators
------------------

The three parallel iterator functions discussed below are designed to
work in conjunction with analysis that makes use of
:ref:`analysis-fields`. Minimally, they can be used to iterate over
trees and nodes in parallel, but their main advantage is that they
will handle the gathering and organization of new analysis field
values so they can be properly saved and reloaded. The most efficient
function to use will depend on the nature of your analysis.

In the examples below, the "analysis" performed will be
facilitated through an :ref:`analysis field <analysis-fields>`, called
"test_field". The following should be assumed to happen before all the
examples.

.. code-block:: python

   import yt
   yt.enable_parallelism()
   import ytree

   a = ytree.load("arbor/arbor.h5")
   if "test_field" not in a.field_list:
       a.add_analysis_field("test_field", default=-1, units="Msun")

.. _tree_parallel:

Parallelizing over Trees
^^^^^^^^^^^^^^^^^^^^^^^^

The :func:`~ytree.utilities.parallel.parallel_trees` function will
distribute a list of trees to be analyzed over all available
processors. Each processor will work on a single tree in
serial.

.. code-block:: python

   trees = list(a[:])
   for tree in ytree.parallel_trees(trees):
       for node in tree["forest"]:
           node["test_field"] = 2 * node["mass"] # this is our analysis

At the end of the outer loop, the new values for "test_field" will be
collected on the root process (i.e., the process with rank 0) and the
arbor will be saved with
:func:`~ytree.data_structures.save_arbor.save_arbor`. No additional
code is required for the new analysis field values to be collected.

By default, each processor will be allocated an equal number of
trees. However, this can lead to an unbalanced load if the amount of
work varies significantly for each tree. By including the
``dynamic=True`` keyword, trees will be allocated using a task queue,
where each processor is only given another tree after it finishes
one. Note, though, that the total number of working processes is one
fewer than the number being run with as one will act as the server for
the task queue.

.. code-block:: python

   trees = list(a[:])
   for tree in ytree.parallel_trees(trees, dynamic=True):
       for node in tree["forest"]:
           node["test_field"] = 2 * node["mass"] # this is our analysis

For various reasons, it may be useful to save results after a certain
number of loop iterations rather than only once at the very end. The
analysis may take a long time, requiring scripts to be restarted, or
keeping results for many trees in memory may be prohibitive. The
``save_every`` keyword can be used to specify a number of iterations
before results are saved. The example below will save results every 8
iterations.

.. code-block:: python

   trees = list(a[:])
   for tree in ytree.parallel_trees(trees, save_every=8):
       for node in tree["forest"]:
           node["test_field"] = 2 * node["mass"] # this is our analysis

The default behavior will allocate a tree to a single processor. To
allocate more than one processor to each tree, the ``njobs`` keyword
can be used to set the total number of process groups for the
loop. For example, if running with 8 total processors, setting
``njobs=4`` will create 4 groups of 2 processors each.

.. code-block:: python

   trees = list(a[:])
   for tree in ytree.parallel_trees(trees, njobs=4):
       for node in tree["forest"]:
           if yt.is_root():
               node["test_field"] = 2 * node["mass"] # this is our analysis

The :func:`~yt.funcs.is_root` function can be used to determine which
process is the root in a group. Only the results recorded by the root
process will be collected. In the example above, it is up to the user
to properly manage the parallelism within the loop.

.. _tree_node_parallel:

Parallelizing over Nodes in a Single Tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The method presented above in :ref:`tree_parallel` works best when the
work done on each node in a tree is small compared to the total number
of trees. If the opposite is true, and either the total number of
trees is small or the work done on each node is expensive, then it may
be better to parallelize over the nodes in a single tree using the
:func:`~ytree.utilities.parallel.parallel_tree_nodes` function. The
previous example is parallelized over nodes in a tree in the following
way.

.. code-block:: python

   trees = list(a[:])
   for tree in trees:
       for node in ytree.parallel_tree_nodes(tree):
           node["test_field"] = 2 * node["mass"]

   if yt.is_root():
       a.save_arbor(trees=trees)

Unlike the :func:`~ytree.utilities.parallel.parallel_trees` and
:func:`~ytree.utilities.parallel.parallel_nodes` functions, no
saving occurs automatically. Hence, the results must be saved
manually, as in the above example.

The ``group`` keyword can be set to ``forest`` (the default),
``tree``, or ``prog`` to control which nodes of the tree are looped
over. The ``dynamic`` and ``njobs`` keywords have similar behavior as
in :ref:`tree_parallel`.

.. _node_parallel:

Parallelizing over Nodes in a List of Trees
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The previous two examples use a nested loop structure, parallelizing
either the outer loop over trees or the inner loop over nodes in a
given tree. The :func:`~ytree.utilities.parallel.parallel_nodes`
function combines these into a single iterator capable of adding
parallelism to either the loop over trees, nodes in a tree, or
both. With this function, the same example from above becomes:

.. code-block:: python

   trees = list(a[:])
   for node in ytree.parallel_nodes(trees):
       node["test_field"] = 2 * node["mass"]

New analysis field values are collected and saved automatically as
with the :func:`~ytree.utilities.parallel.parallel_trees`
function. Similar to :func:`~ytree.utilities.parallel.parallel_trees`,
the ``save_every`` keyword can be used to control the number of full
trees to be completed before saving results. As well, the ``group``
keyword can be used to control the nodes iterated over in a tree,
similar to how it works in
:func:`~ytree.utilities.parallel.parallel_tree_nodes`. You will likely
be unsurprised to learn that the
:func:`~ytree.utilities.parallel.parallel_nodes` function is
implemented using nested calls to
:func:`~ytree.utilities.parallel.parallel_trees` and
:func:`~ytree.utilities.parallel.parallel_tree_nodes`.

The ``dynamic`` and ``njobs`` keywords also work similarly, only that
they must be specified as tuples of length 2, where the first values
control the loop over trees and the second values control the loop
over nodes in a tree. Using this, it is possible to enable task queues
for both loops (trees and nodes), as in the following example.

.. code-block:: python

   trees = list(a[:])
   for node in ytree.parallel_nodes(trees, save_every=8,
                                    njobs=(3, 0),
                                    dynamic=(True, True)):
       node["test_field"] = 2 * node["mass"]

If the above example is run with 13 processors, the result will be a
task queue with 3 process groups of 4 processors each. Each of those
process groups will work on a single tree using its own task queue,
consisting of 1 server process and 3 worker processes. What a world we
live in.
