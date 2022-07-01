.. _developing:

Developer Guide
===============

``ytree`` is developed using the same conventions as yt. The `yt
Developer Guide <http://yt-project.org/docs/dev/developing/index.html>`_
is a good reference for code style, communication with other developers,
working with git, and issuing pull requests. Below is a brief guide of
aspects that are specific to ``ytree``.

Contributing in a Nutshell
--------------------------

Step zero, get out of that nutshell!

After that, the process for making contributions to ``ytree`` is roughly as
follows:

1. Fork the `main ytree repository <https://github.com/ytree-project/ytree>`__.

2. Create a new branch.

3. Make changes.

4. Run tests. Return to step 3, if needed.

5. Issue pull request.

The `yt Developer Guide
<https://yt-project.org/docs/dev/developing/index.html>`__ and
`github <https://github.com/>`__ documentation will help with the
mechanics of git and pull requests.

Testing
-------

The ``ytree`` source comes with a series of tests that can be run to
ensure nothing unexpected happens after changes have been made. These
tests will automatically run when a pull request is issued or updated,
but they can also be run locally very easily. At present, the suite
of tests for ``ytree`` takes about three minutes to run.

Testing Data
^^^^^^^^^^^^

The first order of business is to obtain the sample datasets. See
:ref:`sample-data` for how to do so. Next, ``ytree`` must be configure to
know the location of this data. This is done by creating a configuration
file in your home directory at the location ``~/.config/ytree/ytreerc``.

.. code-block:: bash

   $ mkdir -p ~/.config/ytree
   $ echo [ytree] > ~/.config/ytree/ytreerc
   $ echo test_data_dir = /Users/britton/ytree_data >> ~/.config/ytree/ytreerc
   $ cat ~/.config/ytree/ytreerc
   [ytree]
   test_data_dir = /Users/britton/ytree_data

This path should point to the outer directory containing all the
sample datasets.

Installing Development Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A number of additional packages are required for testing. These can be
installed with pip from within the ``ytree`` source by doing:

.. code-block:: bash

   $ pip install -e .[dev]

To see how these dependencies are defined, have a look at the
``extras_require`` keyword argument in the ``setup.py`` file.

Run the Tests
^^^^^^^^^^^^^

The tests are run from the top level of the ``ytree`` source.

.. code-block:: bash

   $ pytest tests
   ============================= test session starts ==============================
   platform darwin -- Python 3.6.0, pytest-3.0.7, py-1.4.32, pluggy-0.4.0
   rootdir: /Users/britton/Documents/work/yt/extensions/ytree/ytree, inifile:
   collected 16 items

   tests/test_arbors.py ........
   tests/test_flake8.py .
   tests/test_saving.py ...
   tests/test_treefarm.py ..
   tests/test_ytree_1x.py ..

   ========================= 16 passed in 185.03 seconds ==========================

Adding Support for a New Format
-------------------------------

The :class:`~ytree.data_structures.arbor.Arbor` class is reasonably
generalized such that adding support for a new file format
should be relatively straightforward. The existing frontends
also provide guidance for what must be done. Below is a brief
guide for how to proceed. If you are interested in doing this,
we will be more than happy to help!

Where do the files go?
^^^^^^^^^^^^^^^^^^^^^^

As in yt, the code specific to one file format is referred to as a
"frontend". Within the ``ytree`` source, each frontend is located in
its own directory within ``ytree/frontends``. Name your
directory using lowercase and underscores and put it in there.

To allow your frontend to be directly importable at run-time, add
the name to the ``_frontends`` list in ``ytree/frontends/api.py``.

Building Your Frontend
^^^^^^^^^^^^^^^^^^^^^^

A very good way to build a new frontend is to start with an
existing frontend for a similar type of dataset. To see the variety
of examples, consult the :ref:`internal-classes` section of the
:ref:`api-reference`.

To build a new frontend, you will need to make frontend-specific
subclasses for a few components. A straightforward way to do this
is to start with the script below, loading your data with it. Each
line will run correctly after a distinct phase of the implementation
is completed. As you progress, the next function needing implemented
will raise a ``NotImplementedError`` exception, indicating what
should be done next.

.. code-block:: python

   import ytree

   # Arbor subclass with working _is_valid function
   a = ytree.load(<your data>)

   # Recognizing the available fields
   print (a.field_list)

   # Calculate the number of trees in the dataset
   print (a.size)

   # Create root TreeNode objects
   my_tree = a[0]
   print (my_tree)

   # Query fields for individual trees
   print (my_tree['mass'])

   # Query fields for a whole tree
   print (my_tree['tree', 'mass'])

   # Create TreeNodes for whole tree
   for node in my_tree['tree']:
       print (node)

   # Query fields for all root nodes
   print (a['mass'])

   # Putting it all together
   a.save_arbor()

The components and the files in which they belong are:

1. The :class:`~ytree.data_structures.arbor.Arbor` itself (``arbor.py``).

2. The file i/o (``io.py``).

3. Recognizing frontend-specific fields (``fields.py``).

In addition to this, you will need to add a file called ``__init__.py``,
which will allow your code to be imported. This file should minimally
import the frontend-specific :class:`~ytree.data_structures.arbor.Arbor`
class. For example, the consistent-trees ``__init__.py`` looks like this:

.. code-block:: python

   from ytree.frontends.consistent_trees.arbor import \
       ConsistentTreesArbor

The ``_is_valid`` Function
^^^^^^^^^^^^^^^^^^^^^^^^^^

Within every :class:`~ytree.data_structures.arbor.Arbor` subclass should
appear a method called ``_is_valid``. This function is used by
:func:`~ytree.data_structures.load` to determine if the provided file is
the correct type. This function can examine the file's naming convention
and/or open it and inspect its contents, whatever is required to uniquely
identify your frontend. Have a look at the various examples.

Two Types of Arbors
^^^^^^^^^^^^^^^^^^^

There are generally two types of merger tree data that ``ytree``
ingests:

1. all merger tree data (full trees, halos, etc.) contained within
a single file. These include the ``consistent-trees``,
``consistent-trees-hdf5``, ``lhalotree``, and ``ytree`` frontends.

2. halos in files grouped by redshift (halo catalogs) that contain
the halo id for the descendent halo which lives in the next catalog.
An example of this is the ``rockstar`` frontend.

Depending on your case, different base classes should be subclassed.
This is discussed below. There are also hybrid formats that use
both merger tree and halo catalog files together. An example of this
is the ``ahf`` (Amiga Halo Finder) frontend.

Merger Tree Data in One File (or a few)
#######################################

If this is your case, then the consistent-trees and "ytree" frontends
are the best examples to follow.

In ``arbor.py``, your subclass of :class:`~ytree.data_structures.arbor.Arbor`
should implement two functions, ``_parse_parameter_file`` and ``_plant_trees``.

``_parse_parameter_file``: This is the first thing called when your
dataset is loaded. It is responsible for determining things like
box size, cosmological parameters, and the list of fields.

``_plant_trees``: This function is responsible for creating arrays
of the data required to build all the root
:class:`~ytree.data_structures.tree_node.TreeNode` objects in the
:class:`~ytree.data_structures.arbor.Arbor`. The names of these
attributes are declared in the ``_node_io_attrs`` attribute. For
example, the
:class:`~ytree.frontends.consistent_trees_hdf5.arbor.ConsistentTreesHDF5Arbor`
class names three required attributes: ``_fi``, the data file number in
which this tree lives; ``_si``, the starting index of the section in the
data array corresponding to this tree; and ``_ei``, the ending index in
the data array.

In ``io.py``, you will implement the machinery responsible for
reading field data from disk. You must create a subclass of
the :class:`~ytree.data_structures.io.TreeFieldIO` class and implement
the ``_read_fields`` function. This function accepts a single
root node (a ``TreeNode`` that is the root of a tree) and a list
of fields and should return a dictionary of NumPy arrays for each field.

Halo Catalog-style Data
#######################

If this is your case, then the rockstar and treefarm frontends
are the best examples to follow.

For this type of data, you will subclass the
:class:`~ytree.data_structures.arbor.CatalogArbor` class, which is itself a
subclass of :class:`~ytree.data_structures.arbor.Arbor` designed for this
type of data.

In ``arbor.py``, your subclass should implement two functions,
``_parse_parameter_file`` and ``_get_data_files``. The purpose of
``_parse_parameter_file`` is described above.

``_get_data_files``: This type of data is usually loaded by
providing one of the set of files. This function needs to figure
out how many other files there are and their names and construct a
list to be saved.

In ``io.py``, you will create a subclass of
:class:`~ytree.data_structures.io.CatalogDataFile` and implement two functions:
``_parse_header`` and ``_read_fields``.

``_parse_header``: This function reads any metadata specific to this
halo catalog. For exmaple, you might get the current redshift here.

``_read_fields``: This function is responsible for reading field
data from disk. This should minimally take a list of fields and
return a dictionary with NumPy arrays for each field for all halos
contained in the file. It should also, optionally, take a list of
:class:`~ytree.data_structures.tree_node.TreeNode` instances and return fields
only for them.

Field Units and Aliases (``fields.py``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The :class:`~ytree.data_structures.fields.FieldInfoContainer` class holds
information about field names and units. Your subclass can define
two tuples, ``known_fields`` and ``alias_fields``. The
``known_fields`` tuple is used to set units for fields on disk.
This is useful especially if there is no way to get this information
from the file. The convention for each entry is (name on disk, units).

By creating aliases to standardized names, scripts can be run on
multiple types of data with little or no alteration for
frontend-specific field names. This is done with the ``alias_fields``
tuple. The convention for each entry is (alias name, name on disk,
field units).

.. code-block:: python

   from ytree.data_structures.fields import \
        FieldInfoContainer

   class NewCodeFieldInfo(FieldInfoContainer):
       known_fields = (
           # name on disk, units
           ("Mass", "Msun/h"),
           ("PX", "kpc/h"),
       )

       alias_fields = (
           # alias name, name on disk, units for alias
           ("mass", "Mass", "Msun"),
           ("position_x", "PX", "Mpc/h"),
           ...
       )

You made it!
^^^^^^^^^^^^

That's all there is to it! Now you too can do whatever it is
people do with merger trees. There are probably important things
that were left out of this document. If you find any, please consider
making an addition or opening an issue. If you're stuck anywhere,
don't hesitate to ask for help. If you've gotten this far, we
really want to see you make it to the finish!

Everyone Loves Samples
^^^^^^^^^^^^^^^^^^^^^^

It would be especially great if you could provide a small sample dataset
with your new frontend, something less than a few hundred MB if possible.
This will ensure that your new frontend never gets broken and
will also help new users get started. Once you have some data, make an
addition to the arbor tests by following the example in
``tests/test_arbors.py``. Then, contact Britton Smith to arrange for
your sample data to be added to the `ytree data
<https://girder.hub.yt/#collection/59835a1ee2a67400016a2cda>`__
collection on the `yt Hub <https://girder.hub.yt/>`__.

Ok, now you're totally done. Take the rest of the afternoon off.
