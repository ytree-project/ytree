.. _ytree_parallel:

Parallel Computing with ytree
=============================

At present, ``ytree`` itself is not parallelized, although
parallelizing with `Dask <https://dask.org/>`__ is on the development
roadmap for ytree 3.1. However, parallel merger tree analysis can be
accomplished using the :ref:`parallel computing capabilities of yt
<parallel-computation>`.

.. note:: Before reading this section, consult the
   :ref:`parallel-computation` section of the ``yt`` documentation to
   learn how to configure ``yt`` for running in parallel.

``ytree`` can be run in parallel by making use of the
:func:`~yt.utilities.parallel_tools.parallel_analysis_interface.parallel_objects`
function in ``yt``. This functionality is built on `MPI
<https://en.wikipedia.org/wiki/Message_Passing_Interface>`__, so it
can be used to parallelize analysis across multiple nodes of a
distributed computing system. This function powers the two primary
strategies for parallelizing merger tree analysis:
:ref:`tree_parallel` and :ref:`halo_parallel`. These two can also be
combined for :ref:`multi_parallel`. The most efficient strategy will
depend on the nature of your analysis.

In all cases, scripts must be run with ``mpirun`` to work in
parallel. For example, to run on 4 processors, do:

.. code-block:: bash

   $ mpirun -np 4 python my_analysis.py

where "my_analysis.py" is the name of the script.

.. _tree_parallel:

Parallelizing over Trees
------------------------

In this strategy, parallelism is achieved by distributing the list of
trees to be analyzed over the available processors. Each processor
will work on a single tree in serial. Results for all trees will be
collected at the end and saved by the root process (i.e., the process
with rank 0). In this example, the "analysis" performed will be
facilitated through an :ref:`Analysis Field <analysis-fields>`, called
"test_field". However, the analysis can be anything your heart
desires.

All parallel computation in ``yt`` begins by importing ``yt`` and
calling the
:func:`~yt.utilities.parallel_tools.parallel_analysis_interface.enable_parallelism`
function.

.. code-block:: python

   import yt
   yt.enable_parallelism()
   import ytree

We will then load some data and create an :ref:`analysis field
<analysis-fields>`.

.. code-block:: python

   a = ytree.load("arbor/arbor.h5")
   if "test_field" not in a.field_list:
       a.add_analysis_field("test_field", default=-1, units="Msun")

The serial version of our analysis contains two loops, one over all
trees and another over all halos in each tree. It looks likes the
following:

.. code-block:: python

   for my_tree in a[:]:
       yt.mylog.info(f"Analyzing tree: {my_tree}.")
       for my_halo in my_tree["forest"]:
           my_halo["test_field"] = 2 * my_halo["mass"] # this is our analysis

To parallelize this loop over all trees, we insert a call to
:func:`~yt.utilities.parallel_tools.parallel_analysis_interface.parallel_objects`.

.. code-block:: python

   arbor_storage = {}
   for tree_store, my_tree in yt.parallel_objects(a[:], storage=arbor_storage):
       yt.mylog.info(f"Analyzing tree: {my_tree}.")
       for my_halo in my_tree["forest"]:
           my_halo["test_field"] = 2 * my_halo["mass"] # this is our analysis

       tree_store.result = my_tree.field_data["test_field"]

As we will see below, the ``arbor_storage`` dictionary created at the
top will be used after the loop to combine the results on the root
processor. For each iteration of the loop, we are given a local
storage object, called ``tree_store``. All results we want to return
to the root process are assigned to ``tree_store.result``. In the
above example, the ``field_data`` attribute associated with
``my_tree`` is a dictionary containing recently queried field data,
including our new "test_field". We will assign the entire array of
"test_field" values to the result storage. Using ``yt.mylog.info`` to
print will show us which processor is doing what.

Now, we combine the results on the root process and save the new
field.

.. code-block:: python

   if yt.is_root():
       my_trees = []
       for i, my_tree in enumerate(a[:]):
           my_tree.field_data["test_field"] = arbor_storage[i]
           my_trees.append(my_tree)

       a.save_arbor(trees=my_trees)

The :func:`~yt.funcs.is_root` function can be used to figure out the
root process of a group. By default, entries in the ``arbor_storage``
dictionary are stored by the index of the loop, so for example, entry
``0`` will correspond to the first iteration of the original parallel
loop.

.. _halo_parallel:

Parallelizing over Halos
------------------------

In this strategy, multiple processors work together on a single tree
by splitting up the halos in that tree. This time, we leave the outer
loop over all trees in serial and add
:func:`~yt.utilities.parallel_tools.parallel_analysis_interface.parallel_objects`
to the inner loop.

.. code-block:: python

   my_trees = []
   for my_tree in a[:]:
       if yt.is_root():
           yt.mylog.info(f"Analyzing tree: {my_tree}.")

       tree_storage = {}
       for halo_store, my_halo in yt.parallel_objects(
               my_tree["forest"], storage=tree_storage):
           halo_store.result_id = my_halo.tree_id
           halo_store.result = 2 * my_halo["mass"] # this is our analysis

Just as before, we create a dictionary, called ``tree_storage``, that
will be used to combine the results at the end of the loop. We use the
local results storage, here called ``halo_store``, to store both the
result that we want to keep and an id using
``halo_store.result_id``. We set the result id explicitly to help
re-assemble the results in the correct order. For example, this will
ensure correct collection of results when getting nodes by "tree" or
"prog" as well as "forest". Now, we collect the results for the tree.

.. code-block:: python

   my_trees = []
   # this is the outer loop from above
   for my_tree in a[:]:
       if yt.is_root():
           yt.mylog.info(f"Analyzing tree: {my_tree}.")

       ### code block from above ###

       if yt.is_root():
           for tree_id, result in tree_storage.items():
               my_halo = my_tree.get_node("forest", tree_id)
               my_halo["test_field"] = result

           my_trees.append(my_tree)

   # save the trees
   if yt.is_root():
       a.save_arbor(trees=my_trees)

Note, the above code is inside the outer loop over all trees shown
above. Note as well, to ensure that the tree has all of the new values
for the "test_field", we only need to loop over all the relevant halos
and assign the field value to them. The rest happens under the hood.

.. _multi_parallel:

Multi-level Parallelism
-----------------------

With some care, nested loops with calls to
:func:`~yt.utilities.parallel_tools.parallel_analysis_interface.parallel_objects`
can be created to parallelize over both trees and halos within a
tree. By default,
:func:`~yt.utilities.parallel_tools.parallel_analysis_interface.parallel_objects`
will split the work evenly among all processors, assigning one loop
iteration to a single processor. However, the ``njobs`` keyword allows
us to set explicitly the number of process groups over which to divide
up work. In the example below, we restrict the outer loop to two
process groups by setting ``njobs=2``. For example, if we are running
with four processors, each iteration of the outer loop will be
assigned to two processors working together as a group.

.. code-block:: python

    arbor_storage = {}
    for tree_store, my_tree in yt.parallel_objects(
            a[:], storage=arbor_storage, njobs=2):

        if yt.is_root():
            yt.mylog.info(f"Analyzing tree: {my_tree}.")

        tree_storage = {}
        for halo_store, my_halo in yt.parallel_objects(
                my_tree["forest"], storage=tree_storage):
            halo_store.result_id = my_halo.tree_id
            halo_store.result = 2 * my_halo["mass"] # this is our analysis

        # combine results for this tree
        if yt.is_root():
            for tree_id, result in tree_storage.items():
                my_halo = my_tree.get_node("forest", tree_id)
                my_halo["test_field"] = result
            tree_store.result = my_tree.field_data["test_field"]
        else:
            tree_store.result_id = None

    # combine results for all trees
    if yt.is_root():
        my_trees = []
        for i, my_tree in enumerate(a[:]):
            my_tree.field_data["test_field"] = arbor_storage[i]
            my_trees.append(my_tree)
        a.save_arbor(trees=my_trees)

Note, that we use ``yt.is_root()`` inside the outer loop to combine
results from the inner loop. This is allowed because
:func:`~yt.funcs.is_root` will return True for the root of a process
group, not just the global root process. Within the outer loop, the
root is the first process of each of the two groups of two
processes. Add some calls to ``yt.mylog.info`` to prove this to
yourself.

The code above looks mostly like a combination of the previous two
examples, but with a few notable differences. First, the addition of
the ``njobs`` keyword in the outer loop. Second, when combining the
results of the inner loop over all halos, if we are NOT the root
process, we set ``tree_store.result_id`` to None. Without this, the
results from the non-root processes (that we are not actually
collecting) will clobber those from the root processes and nothing
will be saved.

.. _saving_partial_results:

Saving Intermediate Results
---------------------------

Often the analysis is computationally expensive enough to want to save
results as they come instead of waiting for all halos to be analyzed. This
can be useful if results require a lot of memory or the code takes a
long time to run and you would like to restart from a partially
completed state. In the example below, analysis is performed on blocks
of eight trees at a time. Each block is done in parallel, the results
are saved, and analysis resumes.

.. code-block:: python

   a = ytree.load("arbor/arbor.h5")
   if "test_field" not in a.field_list:
       a.add_analysis_field("test_field", default=-1, units="Msun")

   block_size = 8
   my_trees = list(a[:])
   n_blocks = int(np.ceil(len(my_trees) / block_size))

   for ib in range(n_blocks):
       start = ib * block_size
       end = min(start + block_size, len(my_trees))

       tree_storage = {}
       for tree_store, itree in yt.parallel_objects(
               range(start, end), storage=tree_storage, dynamic=False):
           my_tree = my_trees[itree]

           for my_halo in my_tree["tree"]:
               my_halo["test_field"] = 2 * my_halo["mass"]

           tree_store.result_id = itree
           tree_store.result = my_tree.field_data["test_field"]

       if yt.is_root():
           # re-assemble results on root processor
           for itree, results in sorted(tree_storage.items()):
               my_tree = my_trees[itree]
               my_tree.field_data["test_field"] = results

           a.save_arbor(trees=my_trees)

           # now reload it and restore the list of trees
           a = ytree.load(a.filename)
           my_trees = list(a[:])

There are some notable differences between this example and those
above. First, we explicitly create a list of trees with ``my_trees =
list(a[:])`` so we can restore it after saving and reloading. Second,
we loop over ``range(start, end)`` instead of over trees so we can
loop over a block of trees at a time.

Like with most things, more is possible than what is shown here and
there are other ways to do what is demonstrated. Parallel computing
can be very satisfying. Enjoy!
