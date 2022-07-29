.. _examples:

Example Applications
====================

Below are some examples demonstrating interesting combinations of
``ytree`` functionality. Each of the scripts shown below can be
found in the ``doc/source/examples`` directory. If you have made
something not seen here, please considering :ref:`adding it to this
document <developing>`.

Plot the Tree of the Most Massive Halo
--------------------------------------

Below we make a plot of the most massive halo in the arbor. We use the
NumPy :func:`argmax <numpy.argmax>` function to get the index within
the arbor of the most massive halo.

.. literalinclude :: examples/plot_most_massive.py
   :language: python

We use the :attr:`~ytree.visualization.tree_plot.TreePlot.min_mass_ratio`
attribute to plot only halos with masses of at least 10\ :sup:`-3` of the
main halo.

Plot the Tree with the Most Halos
---------------------------------

Similar to above, it is often useful to find the tree containing the
most halos. To do this, we make an array containing the sizes of all
trees using the
:attr:`~ytree.data_structures.tree_node.TreeNode.tree_size` attribute
of the :class:`~ytree.data_structures.tree_node.TreeNode` class. The
:class:`~ytree.data_structures.arbor.Arbor` class's
:attr:`~ytree.data_structures.arbor.Arbor.arr` method is useful for
creating :class:`unyt_array <unyt.array.unyt_array>` objects with
the unit system of the dataset.

.. literalinclude :: examples/plot_most_halos.py
   :language: python

Halo Age (a50)
--------------
Script: `halo_age.py <_static/halo_age.py>`__

One way to define the age of a halo is by calculating the scale factor
when it reached 50% of its current mass. This is often referred to as
"a50". In the example below, this is calculated by linearly
interpolating from the mass of the main progenitor.

.. literalinclude :: examples/halo_age.py
   :language: python
   :lines: 8,12-29

Then, we setup an :ref:`Analysis Pipeline <analysis>` including this
function and use :func:`~ytree.utilities.parallel.parallel_nodes`
to loop over all halos in the dataset in parallel. Finally, we
reload the saved data and print the age of the first halo.

.. literalinclude :: examples/halo_age.py
   :language: python
   :lines: 9-11,31-

Significance
------------

Brought to you by John Wise, a halo's significance is calculated by
recursively summing over all ancestors the mass multiplied by the time
between snapshots. When determining the main progenitor of a halo, the
significance measure will select for the ancestor with the deeper
history instead of just the higher mass. This can be helpful in cases
of near 1:1 mergers.

Below, we define a function that calculates the significance
for every halo in a single tree.

.. code-block:: python

   def calc_significance(node):
      if node.descendent is None:
          dt = 0. * node["time"]
      else:
          dt = node.descendent["time"] - node["time"]

      sig = node["mass"] * dt
      if node.ancestors is not None:
          for anc in node.ancestors:
              sig += calc_significance(anc)

      node["significance"] = sig
      return sig

Now, we'll use the :ref:`analysis_pipeline` to calculate the
significance for all trees and save a new dataset. After loading the
new arbor, we use the
:func:`~ytree.data_structures.arbor.Arbor.set_selector` function to
use the new significance field to determine the progenitor line.

.. code-block:: python

   >>> a = ytree.load("tiny_ctrees/locations.dat")
   >>> a.add_analysis_field("significance", "Msun*Myr")

   >>> ap = ytree.AnalysisPipeline()
   >>> ap.add_operation(calc_significance)

   >>> trees = list(a[:])
   >>> for tree in trees:
   ...     ap.process_target(tree)

   >>> fn = a.save_arbor(filename="significance", trees=trees)
   >>> a2 = ytree.load(fn)
   >>> a2.set_selector("max_field_value", "significance")
   >>> prog = list(a2[0]["prog"])
   >>> print (prog)
   [TreeNode[1457223360], TreeNode[1452164856], TreeNode[1447024182], ...
    TreeNode[6063823], TreeNode[5544219], TreeNode[5057761]]