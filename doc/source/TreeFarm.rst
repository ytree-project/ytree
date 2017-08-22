.. _treefarm:

Making Merger-trees from Gadget FoF/Subfind
===========================================

The ytree ``TreeFarm`` can compute merger-trees either for all halos,
starting at the beginning of the simulation, or for specific halos,
starting at the final output and moving backward.  These two
use-cases are covered separately.  Halo catalogs must be in the form
created by the Gadget FoF halo finder or Subfind substructure
finder.

Computing a Full Merger-tree
----------------------------

``TreeFarm`` accepts a ``yt`` time-series object over which the
merger-tree will be computed.

.. code-block:: python

   import yt
   import ytree

   ts = yt.DatasetSeries("data/groups_*/*.0.hdf5")
   my_tree = ytree.TreeFarm(ts)
   my_tree.trace_descendents("Group", filename="all_halos/")

The first argument to ``trace_descendents`` specifies the type
of halo object to use.  This will typically be either "Group" for
FoF groups or Subhalo for Subfind groups.
This process will create a new halo catalogs with the additional
field representing the descendent ID for each halo.  These can
be loaded using ``yt`` like any other catalogs.  Once complete,
the final merger-tree can be
:ref:`loaded into ytree <load-treefarm>`.

.. _ancestor_search:

Computing a Targeted Merger-tree
--------------------------------

Computing a full merger-tree can be extremely expensive when
the simulation is large.  Instead, merger-trees can be created
for specific halos in the final dataset, then working backward.
Below is an example of computing the merger-tree for only the
most massive halo.

.. code-block:: python

   import yt
   import ytree

   ds = yt.load("fof_subfind/groups_025/fof_subhalo_tab_025.0.hdf5")
   i_max = np.argmax(ds.r["Group", "particle_mass"])
   my_id = ds.r["particle_identifier"][i_max]

   ts = yt.DatasetSeries("data/groups_*/*.0.hdf5")
   my_tree = ytree.TreeFarm(ts)
   my_tree.trace_ancestors("Group", my_id, filename="my_halo/")

Just as above, the resulting catalogs can then be loaded into
a :ref:`TreeFarm Arbor <load-treefarm>`.

Optimizing Merger-tree Creation
-------------------------------

Computing merger-trees can often be an expensive task.  Below
are some tips for speeding up the process.

Running in Parallel
^^^^^^^^^^^^^^^^^^^

ytree uses the parallel capabilities of ``yt`` to divide up the
halo ancestor/descendent search over multiple processors.
In order to do this, ``yt`` must be set up to run in parallel.
See `here <http://yt-project.org/doc/analyzing/parallel_computation.html#setting-up-parallel-yt>`_
for instructions.  Once this is done, a call to
``yt.enable_parallelism()`` must be added to your script.

.. code-block:: python

   import yt
   yt.enable_parallelism()
   import ytree

   ts = yt.DatasetSeries("data/groups_*/*.0.hdf5")
   my_tree = ytree.TreeFarm(ts)
   my_tree.trace_descendents("Group", filename="all_halos/")

That script must then be run with mpirun.

.. code-block:: bash

    mpirun -np 4 python my_script.py

Optimizing Halo Candidate Selection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Halo ancestors and descendents are typically found by comparing
particle IDs between two halos.  The method of selecting which
halos should be compared can greatly affect performance.  By
default, ``TreeFarm`` will compare a halo against all halos
in the next dataset.  This is both the most robust and slowest
method of matching ancestors and descendents.  A smarter
method is to select candidate matches from only a region
around the target halo.  For example, ``TreeFarm`` can be
configured to select halos from a sphere centered on the
current halo.

.. code-block:: python
   :emphasize-lines: 2

   my_tree = ytree.TreeFarm(ts)
   my_tree.set_selector("sphere", "virial_radius", factor=5)
   my_tree.trace_descendents("Group", filename="all_halos/")

In the above example, candidate halos will be selected from a
sphere that is five times the value of the "virial_radius" field.
While this will speed up the calculation, a match will not be
found if the ancestor/descendent is outside of this region.
Some experimentation is recommended to find the optimal balance
between speed and robustness.

Currently, the "sphere" selector is the only other selection
method implemented, although others can be created easily.
For an example, see :func:`~ytree.halo_selector.sphere_selector`.

Searching for Fewer Ancestors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When computing a merger-tree for specific halos
(:ref:`ancestor_search`), you only be interested in the most
massive or the few most massive progenitors.  If this is the
case, ``TreeFarm`` can be configured to end the ancestor
search when these have been found, rather than searching for
all possible progenitors.

The ``set_ancestry_filter`` function places a filter on which
ancestors of any given halo will be returned and followed in
successive rounds of the merger-tree process.  The
"most_massive" filter instructs the ``TreeFarm`` to only
keep the most massive ancestor.  This will greatly reduce
the number of halos included in the merger-tree and,
therefore, speed up the calculation considerably.  For an
example of how to create a new filter, see
:func:`~ytree.ancestry_filter.most_massive`.

The filtering will only occur after all candidates have been
checked for ancestry.  An additional operation an be added to
end the ancestry search after certain criteria have been met.
In the call to ``set_ancestry_short`` below, the ancestry
search will end as soon as an ancestor with at least 50% of
the mass of the target halo has been found.  For an example
of how to create a new function of this type, see
:func:`~ytree.ancestry_short.most_massive`.

.. code-block:: python
   :emphasize-lines: 4, 5

   ts = yt.DatasetSeries("data/groups_*/*.0.hdf5")
   my_tree = ytree.TreeFarm(ts)
   my_tree.trace_ancestors("Group", my_id, filename="my_halo/")
   my_tree.set_ancestry_filter("most_massive")
   my_tree.set_ancestry_short("above_mass_fraction", 0.5)
