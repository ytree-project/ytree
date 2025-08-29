.. _loading:

Loading Data
============

Below are instructions for loading all supported datasets. All examples
use the freely available :ref:`sample-data`.

.. _load-ahf:

Amiga Halo Finder
-----------------

There are two main ways that the `Amiga Halo Finder
<http://popia.ft.uam.es/AHF/>`__ will output merger tree information.
Most AHF outputs will contain a series of files (one per snapshot) linking
a halo in that snapshot with its progenitors. These usually, but not always,
have file names ending in ".AHF_mtree". See :ref:`ahf-naming` if these
files have different names in your data. The second way is to create
a single file containing descendent/ancestor links for all halos from
all snapshots. This file usually starts with "MergerTree\_" and ends
with "-CRMratio2". As long as your data contains one of the above,
everything should be fine even if the naming conventions are slightly
different.

Both formats save a series of files associated with each
snapshot. Parameters are stored in ".parameters" and ".log" files and
halo properties (i.e., all the fields) in ".AHF_halos" files. Make
sure to keep all these files together in the same directory.

If you have the one big file starting with "MergerTree\_" and ending
with "-CRMratio2", use that to load the data.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("AHF_100_tiny/MergerTree_GIZMO-NewMDCLUSTER_0047.txt-CRMratio2")

``ytree`` will then try to guess the naming convention for the
parameter files based on the name of the one big file or on the
available files ending in ".parameter". An exception will be raised if
neither of these methods are able to locate a parameter file. If this
is the case, provide one using the ``parameter_filename`` keyword.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("AHF_100_tiny/MergerTree_GIZMO-NewMDCLUSTER_0047.txt-CRMratio2",
                      parameter_filename="AHF_100_tiny/GIZMO-NewMDCLUSTER_0047.snap_128.parameter")

If you don't have the one big file, then provide the name of the first
".parameter" file.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("ahf_halos/snap_N64L16_000.parameter",
   ...                hubble_constant=0.7)

.. _ahf-naming:

AHF data with different naming conventions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Occasionally, the naming conventions for various files will differ
from the above. Sometimes, the arbor will appear to load correctly,
but all the trees will appear as singular objects with no descendents
or ancestors. Other times, you may see an error the first time you try
to query a tree. Two known variations are:

#. Different file prefixes for the halo catalog and merger tree
   files. For example, one set of files starting with "AHF" and the
   other starting with "MTREE".
#. The mtree data in files not ending in ".AHF_mtree". In this case,
   there still may be files with this suffix, but they may not contain
   the data that ``ytree`` is looking for. The files needed for this
   should look something like below:

.. code-block::

   #   HaloID(1)   HaloPart(2)  NumProgenitors(3)
   #      SharedPart(1)    HaloID(2)   HaloPart(3)
   0  29769  12
     29221  0  29918
     1652  17  1652
     362  90  362

In the example below, this data is located in files ending with
".AHF_croco". The ``name_config`` keyword can be used to specify a
dictionary of naming conventions:

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load(
   >>>     "B25_N256_CDM_1LPT/AHF.B25_N256_CDM_1LPT.snap_055.parameter",
   >>>     name_config={"ahf_prefix": "AHF.B25_N256_CDM_1LPT",
   >>>                  "mtree_prefix": "MTREE.B25_N256_CDM_1LPT.z39_adapt",
   >>>                  "mtree_suffix": ".AHF_croco"})

Valid entries for the ``name_config`` dictionary are "ahf\_prefix",
"mtree\_prefix", and "mtree\_suffix". When using AHF to create merger
trees, it is advisable to use settings that result in file layouts
like those described here.

.. note:: Four important notes about loading AHF data:

          1. The dimensionless Hubble parameter is not provided in AHF
             outputs.  This should be supplied by hand using the
             ``hubble_constant`` keyword. The default value is 1.0.

          2. If the ".log" file is named in a unconventional way or cannot
             be found for some reason, its path can be specified with the
             ``log_filename`` keyword argument. If no log file exists,
             values for ``omega_matter``, ``omega_lambda``, and ``box_size``
             (in units of Mpc/h) can be provided with keyword arguments
             named thusly.

          3. There will be no ".AHF_mtree" file for index 0 as the
             ".AHF_mtree" files store links between files N-1 and N.

          4. ``ytree`` is able to load data where the graph has been
             calculated instead of the tree. However, even in this case,
             only the tree is preserved in ``ytree``. See the `Amiga Halo
             Finder Documentation
             <http://popia.ft.uam.es/AHF/files/AHF.pdf>`_
             for a discussion of the difference between graphs and trees.

.. _load-ctrees:

Consistent-Trees
----------------

The `consistent-trees <https://bitbucket.org/pbehroozi/consistent-trees>`__
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

.. _load-ctrees-hdf5:

Consistent-Trees-HDF5
---------------------

`Consistent-Trees-HDF5 <https://github.com/uchuuproject/uchuutools>`__
is a variant of the consistent-trees format built on HDF5. It is used by
the `Skies & Universe <http://www.skiesanduniverses.org/>`_ project.
This format allows for access by either *forests* or *trees* as per the
definitions above. The data can be stored as either a struct of arrays
or an array of structs. Both layouts are supported, but ``ytree`` is
currently optimized for the struct of arrays layout. Field access with
struct of arrays will be 1 to 2 orders of magnitude faster than with
array of structs.

Datasets from this format consist of a series of HDF5 files with the
naming convention, "forest.h5", "forest_0.5", ..., "forest_N.h5".
The numbered files contain the actual data while the "forest.h5" file
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

Access by Forest
^^^^^^^^^^^^^^^^

By default, ``ytree`` will load consistent-trees-hdf5 datasets to
provide access to each tree, such that ``a[N]`` will return the Nth
tree in the dataset and ``a[N]["tree"]`` will return all halos in
that tree. However, by providing the ``access="forest"`` keyword to
:func:`~ytree.data_structures.load.load`, data will be loaded
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
forest. See :ref:`forest-access` for how to locate all individual
trees in a forest.

.. _load-gadget4:

Gadget4
-------

The `Gadget4
<https://wwwmpa.mpa-garching.mpg.de/gadget4/09_special_modules/#merger-trees>`__
format consists of one or more HDF5 files. Each file contains
information on the trees contained within as well as some or all of
the associated field data for those trees. Field data for large trees
can span multiple data files and the start of any file does not
necessarily correspond to the start of field data for the trees it
holds. This format supports :ref:`forest-access`.

To load single-file data, load with the path to that file.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("gadget4/trees/trees.hdf5")

To load a dataset consisting of multiple files, provide the path to
the zeroth file.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("gadget4/treedata/trees.0.hdf5")

For multi-file datasets, all data files must be present for the
dataset to be loaded. It is not possible to load a subseta
multi-file dataset. Because data for any given tree is only loaded
when needed, there is little benefit to trying to load a subset of
the full data. However, if you really want to limit your dataset to
a selection of the full data, your best bet is to save just the
trees you want to a new dataset using the
:func:`~ytree.data_structures.arbor.Arbor.save_arbor` function.
See :ref:`saving-trees` for more information.

.. _load-csv:

Generic CSV Data
----------------

``ytree`` can load tree data from a `CSV
<https://en.wikipedia.org/wiki/Comma-separated_values>`__ file
provided that the file defines two fields:

#. "uid" - a universal ID of an item
#. "desc_uid" - the uid of the item's direct descendent

The CSV file must have a specific format in which the first three
lines start with the "#" character and define the field names, data
types, and units. As in standard CSV behavior, spaces are interpreted
literally in the case of non-numeric data (i.e., a line with "...,
something,..." will result in a value of " something" and not "something").

.. code-block:: bash

   #uid,desc_uid,name,time,charisma
   #INT,INT,STR,FLOAT,FLOAT
   #None,None,None,yr,G
   1,4,Jen-Luc,2305,144.70137425
   2,4,William,2335,98.73156766
   3,4,Beverly,2324,127.979825
   4,6,Deanna,2336,131.83806431
   5,6,Thomas,2335,172.14870662
   6,-1,Tasha,2337,80.64762619
   7,9,Lwaxana,2305,120.59923579

The supported data types are:

* FLOAT: float
* INT: integer
* STR: string

All `units supported by the unyt package
<https://unyt.readthedocs.io/en/stable/unit_listing.html>`__
are valid. The word "None" can be used to denote unitless
fields. *String fields must be unitless.* Also note, if the data does
not include a "mass" field, another field must be specified for
progenitor identification (see :ref:`custom-progenitor`).

.. code-block:: python

   >>> a = ytree.load("csv/trees.csv")
   >>> a.set_selector("max_field_value", "charisma")

.. _load-lhalotree:

LHaloTree
---------

The `LHaloTree <http://adsabs.harvard.edu/abs/2005Natur.435..629S>`__
format is typically one or more files with a naming convention like
"trees_063.0" that contain the trees themselves and a single file
with a suffix ".a_list" that contains a list of the scale factors
at the time of each simulation snapshot.

.. note:: The LHaloTree format loads halos by forest. There is no need
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

.. _load-lhalotree-hdf5:

LHaloTree-HDF5
--------------

This is the same algorithm as :ref:`load-lhalotree`, except with data
saved in HDF5 files instead of unformatted binary. LHaloTree-HDF5 is
one of the formats used by the
`Illustris-TNG project <https://www.tng-project.org/>`__ and is
described in detail
`here <https://www.tng-project.org/data/docs/specifications/#sec4b>`__.
Like :ref:`load-lhalotree`, this format supports :ref:`accessing trees
by forest <forest-access>`. The LHaloTree-HDF5 format stores trees in
multiple HDF5 files contained within a single directory. Each tree is
fully contained within a single file, so loading is possible even when
only a subset of all files is present. To load, provide the path to
one file.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("TNG50-4-Dark/trees_sf1_099.0.hdf5")

The files do not contain information on the box size and cosmological
parameters of the simulation, but they can be provided by hand, with
the box size assumed to be in units of comoving Mpc/h.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("TNG50-4-Dark/trees_sf1_099.0.hdf5",
   ...                box_size=35, hubble_constant=0.6774,
   ...                omega_matter=0.3089, omega_lambda=0.6911)

The LHaloTree-HDF5 format contains multiple definitions of halo mass
(see `here <https://www.tng-project.org/data/docs/specifications/#sec4b>`__),
and as such, the field alias "mass" is not defined by default. However,
the :ref:`alias can be created <alias-fields>` if one is preferable. This
is also necessary to facilitate :ref:`progenitor-access`.

.. code-block:: python

   >>> a.add_alias_field("mass", "Group_M_TopHat200", units="Msun")

.. _load-moria:

MORIA
-----

`MORIA <https://bdiemer.bitbucket.io/sparta/analysis_moria.html>`__ is a
merger tree extension of the
`SPARTA <https://bdiemer.bitbucket.io/sparta/index.html>`__ code
(`Diemer 2017 <https://ui.adsabs.harvard.edu/abs/2017ApJS..231....5D/>`__;
`Diemer 2020a <https://ui.adsabs.harvard.edu/abs/2020ApJS..251...17D/>`__).
An output from MORIA is a single HDF5 file, whose path should be provided
for loading.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("moria/moria_tree_testsim050.hdf5")

Merger trees in MORIA are organized by :ref:`forest <forest-access>`, so
printing ``a.size`` (following the example above) will give the number of
forests, not the number of trees. MORIA outputs contain multiple definitions
of halo mass (see `here
<https://bdiemer.bitbucket.io/sparta/analysis_moria_output.html#complete-list-of-catalog-tree-fields-in-erebos-catalogs>`__),
and as such, the field alias "mass" is not defined by default. However,
the :ref:`alias can be created <alias-fields>` if one is preferable. This
is also necessary to facilitate :ref:`progenitor-access`.

.. code-block:: python

   >>> a.add_alias_field("mass", "Mpeak", units="Msun")

On rare occasions, a halo will be missing from the output even though
another halo claims it as its descendent. This is usually because the
halo has dropped below the minimum mass to be included. In these cases,
MORIA will reassign the halo's descendent using the ``descendant_index``
field (see discussion in `here
<https://bdiemer.bitbucket.io/sparta/analysis_moria_output.html>`__).
If ``ytree`` encounters such a situation, a message like the one below
will be printed.

.. code-block:: python

   >>> t = a[85]
   >>> print (t["tree", "Mpeak"])
   ytree: [INFO     ] 2021-05-04 15:29:19,723 Reassigning descendent of halo 374749 from 398837 to 398836.
   [1.458e+13 1.422e+13 1.363e+13 1.325e+13 1.295e+13 1.258e+13 1.212e+13 ...
    1.309e+11 1.178e+11 1.178e+11 1.080e+11 9.596e+10 8.397e+10] Msun/h

.. _load-rockstar:

Rockstar Catalogs
-----------------

`Rockstar <https://bitbucket.org/gfcstanford/rockstar>`__
catalogs with the naming convention "out_*.list" will contain
information on the descendent ID of each halo and can be loaded
independently of consistent-trees.  This can be useful when your
simulation has very few halos, such as in a zoom-in simulation.  To
load in this format, simply provide the path to one of these files.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("rockstar/rockstar_halos/out_0.list")

.. _load-treefarm:

TreeFarm
--------

Merger trees created with `treefarm <https://treefarm.readthedocs.io/>`__
can be loaded in by providing the path to one of the catalogs created
during the calculation.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("tree_farm/tree_farm_descendents/fof_subhalo_tab_000.0.h5")

.. _load-treefrog:

TreeFrog
--------

`TreeFrog <https://github.com/pelahi/TreeFrog>`__ generates merger trees
primarily for `VELOCIraptor <https://github.com/pelahi/VELOCIraptor-STF>`__
halo catalogs. The TreeFrog format consists of a series of HDF5 files.
One file contains meta-data for the entire dataset. The other files contain
the tree data, split into HDF5 groups corresponding to the original halo
catalogs. To load, provide the path to the "foreststats" file, i.e., the
one ending in ".hdf5".

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("treefrog/VELOCIraptor.tree.t4.0-131.walkabletree.sage.forestID.foreststats.hdf5")

Merger trees in TreeFrog are organized by :ref:`forest <forest-access>`, so
printing ``a.size`` (following the example above) will give the number of
forests. Note, however, the id of the root halo for any given forest is not
the same as the forest id.

.. code-block:: python

    >>> my_tree = a[0]
    >>> print (my_tree["uid"])
    131000000000001
    >>> print (my_tree["ForestID"])
    104000000011727

TreeFrog outputs contain multiple definitions of halo mass, and as such, the field
alias "mass" is not defined by default. However, the :ref:`alias can be created
<alias-fields>` if one is preferable. This is also necessary to facilitate
:ref:`progenitor-access`.

.. code-block:: python

   >>> a.add_alias_field("mass", "Mass_200crit", units="Msun")

.. _load-ytree:

Saved Arbors (ytree format)
---------------------------

Once merger tree data has been loaded, it can be saved to a
universal format using :func:`~ytree.data_structures.arbor.Arbor.save_arbor` or
:func:`~ytree.data_structures.tree_node.TreeNode.save_tree`. These can be loaded
by providing the path to the primary HDF5 file.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("arbor/arbor.h5")

See :ref:`saving-trees` for more information on saving arbors and trees.
