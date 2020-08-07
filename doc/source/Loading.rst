.. _loading:

Loading Data
============

Below are instructions for loading all supported datasets. All examples
use the freely available :ref:`sample-data`.

Amiga Halo Finder
-----------------

The `Amiga Halo Finder <http://popia.ft.uam.es/AHF/Download.html>`_ format
stores data in a series of files, with one each per snapshot.  Parameters
are stored in ".parameters" and ".log" files, halo information in
".AHF_halos" files, and descendent/ancestor links are stored in ".AHF_mtree"
files.  Make sure to keep all of these together.  To load, provide the name
of the first ".parameter" file.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("ahf_halos/snap_N64L16_000.parameter",
   ...                hubble_constant=0.7)

.. note:: Three important notes about loading AHF data:

          1. The dimensionless Hubble parameter is not provided in AHF
             outputs.  This should be supplied by hand using the
             ``hubble_constant`` keyword. The default value is 1.0.

          2. There will be no ".AHF_mtree" file for index 0 as the
             ".AHF_mtree" files store links between files N-1 and N.

          3. ``ytree`` is able to load data where the graph has been
             calculated instead of the tree. However, even in this case,
             only the tree is preserved in ``ytree``. See the `Amiga Halo
             Finder Documentation
             <http://popia.ft.uam.es/AHF/Documentation.html>`_
             for a discussion of the difference between graphs and trees.

Consistent-Trees
----------------

The `consistent-trees <https://bitbucket.org/pbehroozi/consistent-trees>`_
format consists of a set of files called "locations.dat", "forests.list",
at least one file named something like "tree_0_0_0.dat". For large
simulations, there may be a number of these "tree_*.dat" files. After
running Rockstar and consistent-trees, these will most likely be located in
the "rockstar_halos/trees" directory. The full data set can be loaded by
providing the path to the *locations.dat* file.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("tiny_ctrees/locations.dat")

Alternatively, data from a single tree file can be loaded by providing the
path to that file.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("consistent_trees/tree_0_0_0.dat")

Consistent-Trees hlist Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While running consistent-trees, a series of files will be created in the
"rockstar_halos/hlists" directory with the naming convention,
"hlist_<scale-factor>.list". These are the catalogs that will be combined
to make the final output files. However, these files contain roughly 30
additional fields that are not included in the final output. Merger trees
can be loaded by providing the path to the first of these files.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("ctrees_hlists/hlists/hlist_0.12521.list")

.. note:: Note, loading trees with this method will be slower than using
   the standard consistent-trees output file as ``ytree`` will have to
   assemble each tree across multiple files. This method is not
   recommended unless the additional fields are necessary.

Consistent-Trees-HDF5
---------------------

`Consistent-Trees-HDF5 <https://github.com/uchuuproject/uchuutools>`__
is a variant of the consistent-trees format built on HDF5. It is used by
the `Skies & Universe <http://www.skiesanduniverses.org/>`_ project.
This format allows for access by either `forests` or `trees` as per the
definitions above. This data can be stored as either structs of arrays
or arrays of structs. Currently, ``ytree`` only supports the structs of
arrays format.

Datasets from this format consist of a series of HDF5 files with the
naming convention, `forest.h5`, `forest_0.5`, ..., `forest_N.h5`.
The numbered files contain the actual data while the `forest.h5` file
contains virtual datasets that point to the data files. To load all
the data, provide the path to the virtual dataset file:

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("consistent_trees_hdf5/soa/forest.h5")

To load a subset of the full dataset, provide a single data file or
a list/tuple of files.

.. code-block:: python

   >>> import ytree
   >>> # single file
   >>> a = ytree.load("consistent_trees_hdf5/soa/forest_0.h5")
   >>> # multiple data files (sample data only has one)
   >>> a = ytree.load(["forest_0.h5", "forest_1.h5"])

.. _ctree-hdf5-forest:

Access by Forest
^^^^^^^^^^^^^^^^

By default, ``ytree`` will load consistent-trees-hdf5 datasets to
provide access to each tree, such that ``a[N]`` will return the Nth
tree in the dataset and ``a[N]["tree"]`` will return all halos in
that tree. However, by providing the ``access="forest"`` keyword to
:func:`~ytree.data_structures.arbor.load`, data will be loaded
according to the forest it belongs to.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("consistent_trees_hdf5/soa/forest.h5",
   ...                access="forest")

In this mode, ``a[N]`` will return the Nth forest and
``a[N]["forest"]`` will return all halos in that forest. In
forest access mode, the "root" of the forest, i.e., the
:class:`~ytree.data_structures.tree_node.TreeNode` object returned
by doing ``a[N]`` will be the root of one of the trees in that
forest. To find all of the roots in that forest, i.e., the start
of all individual trees contained, one can do:

.. code-block:: python

   >>> my_forest = a[0]
   >>> desc_uids = np.array(list(my_forest["forest", "desc_uid"]))
   >>> roots = [node for node in f["forest"] if node["desc_uid"] == -1]
   >>> print (roots)
   [TreeNode[90049568], TreeNode[89739051]]
   >>> # all halos in first tree
   >>> print (list(roots[0]["tree"]))
   [TreeNode[90049568], TreeNode[88202573], TreeNode[86292249], ...
    TreeNode[13635225], TreeNode[11545001], TreeNode[9538546]]

Rockstar Catalogs
-----------------

Rockstar catalogs with the naming convention "out_*.list" will contain
information on the descendent ID of each halo and can be loaded
independently of consistent-trees.  This can be useful when your
simulation has very few halos, such as in a zoom-in simulation.  To
load in this format, simply provide the path to one of these files.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("rockstar/rockstar_halos/out_0.list")

LHaloTree
---------

The `LHaloTree <http://adsabs.harvard.edu/abs/2005Natur.435..629S>`_
format is typically one or more files with a naming convention like
"trees_063.0" that contain the trees themselves and a single file
with a suffix ".a_list" that contains a list of the scale factors
at the time of each simulation snapshot.

.. note:: The LHaloTree format loads halos by forest. A similar
   strategy as described in :ref:`ctree-hdf5-forest` can be used
   for accessing all trees in a given forest. There is no need
   to provide the ``access="forest"`` keyword here.

In addition to the LHaloTree files, ``ytree`` also requires additional
information about the simulation from a parameter file (in
`Gadget <http://wwwmpa.mpa-garching.mpg.de/gadget/>`_ format). At
minimum, the parameter file should contain the cosmological parameters
``HubbleParam, Omega0, OmegaLambda, BoxSize, PeriodicBoundariesOn,``
and ``ComovingIntegrationOn``, and the unit parameters
``UnitVelocity_in_cm_per_s, UnitLength_in_cm,`` and ``UnitMass_in_g``.
If not specified explicitly (see below), a file with the extension
".param" will be searched for in the directory containing the
LHaloTree files.

If all of the required files are in the same directory, an LHaloTree
catalog can be loaded from the path to one of the tree files.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("lhalotree/trees_063.0")

Both the scale factor and parameter files can be specified explicitly
through keyword arguments if they do not match the expected pattern
or are located in a different directory than the tree files.

.. code-block:: python

   >>> a = ytree.load("lhalotree/trees_063.0",
   ...                parameter_file="lhalotree/param.txt",
   ...                scale_factor_file="lhalotree/a_list.txt")

The scale factors and/or parameters themselves can also be passed
explicitly from python.

.. code-block:: python

   >>> import numpy as np
   >>> parameters = dict(HubbleParam=0.7, Omega0=0.3, OmegaLambda=0.7,
   ...     BoxSize=62500, PeriodicBoundariesOn=1, ComovingIntegrationOn=1,
   ...     UnitVelocity_in_cm_per_s=100000, UnitLength_in_cm=3.08568e21,
   ...     UnitMass_in_g=1.989e+43)
   >>> scale_factors = [ 0.0078125,  0.012346 ,  0.019608 ,  0.032258 ,  0.047811 ,
   ...      0.051965 ,  0.056419 ,  0.061188 ,  0.066287 ,  0.071732 ,
   ...      0.07754  ,  0.083725 ,  0.090306 ,  0.097296 ,  0.104713 ,
   ...      0.112572 ,  0.120887 ,  0.129675 ,  0.13895  ,  0.148724 ,
   ...      0.159012 ,  0.169824 ,  0.181174 ,  0.19307  ,  0.205521 ,
   ...      0.218536 ,  0.232121 ,  0.24628  ,  0.261016 ,  0.27633  ,
   ...      0.292223 ,  0.308691 ,  0.32573  ,  0.343332 ,  0.361489 ,
   ...      0.380189 ,  0.399419 ,  0.419161 ,  0.439397 ,  0.460105 ,
   ...      0.481261 ,  0.502839 ,  0.524807 ,  0.547136 ,  0.569789 ,
   ...      0.59273  ,  0.615919 ,  0.639314 ,  0.66287  ,  0.686541 ,
   ...      0.710278 ,  0.734031 ,  0.757746 ,  0.781371 ,  0.804849 ,
   ...      0.828124 ,  0.851138 ,  0.873833 ,  0.896151 ,  0.918031 ,
   ...      0.939414 ,  0.960243 ,  0.980457 ,  1.       ]
   >>> a = ytree.load("lhalotree/trees_063.0",
   ...                parameters=parameters,
   ...                scale_factors=scale_factors)

.. _load-treefarm:

TreeFarm
--------

Merger-trees created with `treefarm <https://treefarm.readthedocs.io/>`_
can be loaded in by providing the path to one of the catalogs created
during the calculation.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("tree_farm/tree_farm_descendents/fof_subhalo_tab_000.0.h5")

.. _load-ytree:

Saved Arbors
------------

Once merger-tree data has been loaded, it can be saved to a
universal format using :func:`~ytree.data_structures.arbor.Arbor.save_arbor` or
:func:`~ytree.data_structures.tree_node.TreeNode.save_tree`.  These can be loaded by
providing the path to the primary hdf5 file.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("arbor/arbor.h5")
