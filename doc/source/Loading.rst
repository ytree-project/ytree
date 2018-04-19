.. _loading:

Loading Data
============

Below are instructions for loading all supported datasets.

Amiga Halo Finder
-----------------

The `Amiga Halo Finder <http://popia.ft.uam.es/AHF/Download.html>`_ format
stores data in a series of files, with one each per snapshot.  Parameters
are stored in ".parameters" and ".log" files, halo information in
".AHF_halos" files, and descendent/ancestor links are stored in ".AHF_mtree"
files.  Make sure to keep all of these together.  To load, provide the name
of the first ".parameter" file.

.. code-block:: python

   import ytree
   a = ytree.load("ahf_halos/snap_N64L16_000.parameter",
                  hubble_constant=0.7)

.. note:: Three important notes about loading AHF data:

          1. The dimensionless Hubble parameter is not provided in AHF
             outputs.  This should be supplied by hand using the
             ``hubble_constant`` keyword. The default value is 1.0.

          2. There will be no ".AHF_mtree" file for index 0 as the
             ".AHF_mtree" files store links between files N-1 and N.

          3. ytree is able to load data where the graph has been
             calculated instead of the tree. However, even in this case,
             only the tree is preserved in ytree. See the `Amiga Halo
             Finder Documentation
             <http://popia.ft.uam.es/AHF/Documentation.html>`_
             for a discussion of the difference between graphs and trees.

Consistent-Trees
----------------

The `consistent-trees <https://bitbucket.org/pbehroozi/consistent-trees>`_
format is typically one or a few files with a naming convention like
"tree_0_0_0.dat".  To load these files, just give the filename

.. code-block:: python

   import ytree
   a = ytree.load("consistent_trees/tree_0_0_0.dat")

Rockstar Catalogs
-----------------

Rockstar catalogs with the naming convention "out_*.list" will contain
information on the descendent ID of each halo and can be loaded
independently of consistent-trees.  This can be useful when your
simulation has very few halos, such as in a zoom-in simulation.  To
load in this format, simply provide the path to one of these files.

.. code-block:: python

   import ytree
   a = ytree.load("rockstar/rockstar_halos/out_0.list")

LHaloTree
---------

The `LHaloTree <http://adsabs.harvard.edu/abs/2005Natur.435..629S>`_
format is typically one or more files with a naming convention like
"trees_063.0" that contain the trees themselves and a single file
with a suffix ".a_list" that contains a list of the scale factors
at the time of each simulation snapshot.

In addition to the LHaloTree files, ytree also requires additional
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

   import ytree
   a = ytree.load("lhalotree/trees_063.0")

Both the scale factor and parameter files can be specified explicitly
through keyword arguments if they do not match the expected pattern
or are located in a different directory than the tree files.

.. code-block:: python

   a = ytree.load("lhalotree/trees_063.0",
                  parameter_file="lhalotree/param.txt",
		  scale_factor_file="lhalotree/a_list.txt")

The scale factors and/or parameters themselves can also be passed
explicitly from python.

.. code-block:: python

   import numpy as np
   parameters = dict(HubbleParam=0.7, Omega0=0.3, OmegaLambda=0.7,
       BoxSize=62500, PeriodicBoundariesOn=1, ComovingIntegrationOn=1,
       UnitVelocity_in_cm_per_s=100000, UnitLength_in_cm=3.08568e21,
       UnitMass_in_g=1.989e+43)
   scale_factors = [ 0.0078125,  0.012346 ,  0.019608 ,  0.032258 ,  0.047811 ,
        0.051965 ,  0.056419 ,  0.061188 ,  0.066287 ,  0.071732 ,
        0.07754  ,  0.083725 ,  0.090306 ,  0.097296 ,  0.104713 ,
        0.112572 ,  0.120887 ,  0.129675 ,  0.13895  ,  0.148724 ,
        0.159012 ,  0.169824 ,  0.181174 ,  0.19307  ,  0.205521 ,
        0.218536 ,  0.232121 ,  0.24628  ,  0.261016 ,  0.27633  ,
        0.292223 ,  0.308691 ,  0.32573  ,  0.343332 ,  0.361489 ,
        0.380189 ,  0.399419 ,  0.419161 ,  0.439397 ,  0.460105 ,
        0.481261 ,  0.502839 ,  0.524807 ,  0.547136 ,  0.569789 ,
        0.59273  ,  0.615919 ,  0.639314 ,  0.66287  ,  0.686541 ,
        0.710278 ,  0.734031 ,  0.757746 ,  0.781371 ,  0.804849 ,
        0.828124 ,  0.851138 ,  0.873833 ,  0.896151 ,  0.918031 ,
        0.939414 ,  0.960243 ,  0.980457 ,  1.       ]
   a = ytree.load("lhalotree/trees_063.0",
                  parameters=parameters,
                  scale_factors=scale_factors)

.. _load-treefarm:

TreeFarm
--------

Merger-trees created with :ref:`TreeFarm <treefarm>` (ytree's merger-tree 
code for Gadget FoF/SUBFIND catalogs) can be loaded in by providing the
path to one of the catalogs created during the calculation.

.. code-block:: python

   import ytree
   a = ytree.load("tree_farm/tree_farm_descendents/fof_subhalo_tab_000.0.h5")

.. _load-ytree:

Saved Arbors
------------

Once merger-tree data has been loaded, it can be saved to a
universal format using :func:`~ytree.arbor.arbor.Arbor.save_arbor` or
:func:`~ytree.arbor.tree_node.TreeNode.save_tree`.  These can be loaded by
providing the path to the primary hdf5 file.

.. code-block:: python

   import ytree
   a = ytree.load("arbor/arbor.h5")

.. _load-old-arbor:

Saved Arbors from ytree 1.1
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Arbors created with version 1.1 of ytree and earlier can be reloaded by
providing the single file created.  It is recommended that arbors be
re-saved into the newer format as this will significantly improve
performance.

.. code-block:: python

   import ytree
   a = ytree.load("arbor.h5")
