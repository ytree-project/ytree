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

Script: `plot_most_massive.py <_static/plot_most_massive.py>`__

Below we make a plot of the most massive halo in the arbor. We use the
NumPy :func:`argmax <numpy.argmax>` function to get the index within
the arbor of the most massive halo.

.. literalinclude :: examples/plot_most_massive.py
   :language: python
   :lines: 5-

We use the :attr:`~ytree.visualization.tree_plot.TreePlot.min_mass_ratio`
attribute to plot only halos with masses of at least 10\ :sup:`-3` of the
main halo.

Plot the Tree with the Most Halos
---------------------------------

Script: `plot_most_halos.py <_static/plot_most_halos.py>`__

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
   :lines: 5-

Halo Age (a50)
--------------

Script: `halo_age.py <_static/halo_age.py>`__

.. note:: This script includes extra code to make it run within the
   test suite. To run conventionally, remove the lines indicated in
   the header of script.

One way to define the age of a halo is by calculating the scale factor
when it reached 50% of its current mass. This is often referred to as
"a50". In the example below, this is calculated by linearly
interpolating from the mass of the main progenitor.

.. literalinclude :: examples/halo_age.py
   :language: python
   :lines: 30-46

Then, we setup an :ref:`Analysis Pipeline <analysis>` including this
function and use :func:`~ytree.utilities.parallel.parallel_nodes`
to loop over all halos in the dataset in parallel.

.. literalinclude :: examples/halo_age.py
   :language: python
   :lines: 55-64

Finally, we reload the saved data and print the age of the first halo.

.. literalinclude :: examples/halo_age.py
   :language: python
   :lines: 66-68

Do the following to run the script on two processors:

.. code-block:: bash

   $ mpirun -np 2 python halo_age.py

Significance
------------

Script: `halo_significance.py <_static/halo_significance.py>`__

.. note:: This script includes extra code to make it run within the
   test suite. To run conventionally, remove the lines indicated in
   the header of script.

Brought to you by John Wise, a halo's significance is calculated by
recursively summing over all ancestors the mass multiplied by the time
between snapshots. When determining the main progenitor of a halo, the
significance measure will select for the ancestor with the deeper
history instead of just the higher mass. This can be helpful in cases
of near 1:1 mergers.

First, we define a function that calculates the significance
for every halo in a single tree.

.. literalinclude :: examples/halo_significance.py
   :language: python
   :lines: 27-39

Then, we use the :ref:`analysis_pipeline` to calculate the
significance for all trees and save a new dataset. Because the
``calc_significance`` function defined above works on all halos
in a given tree at once, we parallelize this by allocating a whole
tree to each processor using the
:func:`~ytree.utilities.parallel.parallel_trees` function.

.. literalinclude :: examples/halo_significance.py
   :language: python
   :lines: 48-57

After loading the new arbor, we use the
:func:`~ytree.data_structures.arbor.Arbor.set_selector` function to
use the new significance field to determine the progenitor line.

.. literalinclude :: examples/halo_significance.py
   :language: python
   :lines: 59-63

Do the following to run the script on two processors:

.. code-block:: bash

   $ mpirun -np 2 python halo_significance.py

Merger and Smooth Accretion Rates
----------------------------------

Script: `merger_accretion_rates.py <_static/merger_accretion_rates.py>`__

.. note:: This script includes extra code to make it run within the
   test suite. To run conventionally, remove the lines indicated in
   the header of script.

The growth of a dark matter halo can be decomposed into two components:
mass gained through mergers with other halos, and mass gained through
smooth accretion of diffuse material. Below we define a function that
calculates both rates for each halo node.

The merger rate is calculated by summing the masses of all direct
ancestors, subtracting the main progenitor mass, and dividing by
the time between them. The smooth accretion rate is then inferred
as the residual between the total mass growth rate and the merger rate.

.. literalinclude :: examples/merger_accretion_rates.py
   :language: python
   :lines: 35-51

Then, we setup an :ref:`Analysis Pipeline <analysis>` and use
:func:`~ytree.utilities.parallel.parallel_nodes` to loop over all halos
in parallel.

.. literalinclude :: examples/merger_accretion_rates.py
   :language: python
   :lines: 60-70

Do the following to run the script on two processors:

.. code-block:: bash

   $ mpirun -np 2 python merger_accretion_rates.py
