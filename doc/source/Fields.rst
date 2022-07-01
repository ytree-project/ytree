.. _fields:

Fields in ytree
===============

``ytree`` supports multiple types of fields, each representing numerical
values associated with each halo in the
:class:`~ytree.data_structures.arbor.Arbor`. These include the
:ref:`native fields <native-fields>` stored on disk, :ref:`alias fields
<alias-fields>`, :ref:`derived fields <derived-fields>`, and
:ref:`analysis fields <analysis-fields>`.

The Field Info Container
------------------------

Each :class:`~ytree.data_structures.arbor.Arbor` contains a dictionary,
called :func:`~ytree.data_structures.arbor.Arbor.field_info`,
with relevant information for each available field. This information
can include the units, type of field, any dependencies or aliases, and
things relevant to reading the data from disk.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("tree_0_0_0.dat")
   >>> print (a.field_info["Rvir"])
   {'description': 'Halo radius (kpc/h comoving).', 'units': 'kpc/h ', 'column': 11,
    'aliases': ['virial_radius']}
   >>> print (a.field_info["mass"])
   {'type': 'alias', 'units': 'Msun', 'dependencies': ['Mvir']}

.. _native-fields:

Fields on Disk
--------------

Every field stored in the dataset's files should be available within
the :class:`~ytree.data_structures.arbor.Arbor`. The ``field_list``
contains a list of all fields on disk
with their native names.

.. code-block:: python

   >>> print (a.field_list)
   ['scale', 'id', 'desc_scale', 'desc_id', 'num_prog', ...]

.. _alias-fields:

Alias Fields
------------

Because the various dataset formats use different naming conventions for
similar fields, ``ytree`` allows fields to be referred to by aliases. This
allows for a universal set of names for the most common fields. Many are
added by default, including "mass", "virial_radius", "position_<xyz>",
and "velocity_<xyz>". The list of available alias and derived fields
can be found in the ``derived_field_list``.

.. code-block:: python

   >>> print (a.derived_field_list)
   ['uid', 'desc_uid', 'scale_factor', 'mass', 'virial_mass', ...]

Additional aliases can be added with
:func:`~ytree.data_structures.arbor.Arbor.add_alias_field`.

.. code-block:: python

   >>> a.add_alias_field("amount_of_stuff", "mass", units="kg")
   >>> print (a["amount_of_stuff"])
   [  1.30720461e+45,   1.05085632e+45,   1.03025691e+45, ...
   1.72691772e+42,   1.72691772e+42,   1.72691772e+42]) kg

.. _derived-fields:

Derived Fields
--------------

Derived fields are functions of existing fields, including other
derived and alias fields. New derived fields are created by
providing a defining function and calling
:func:`~ytree.data_structures.arbor.Arbor.add_derived_field`.

.. code-block:: python

   >>> def potential_field(field, data):
   ...     # data.arbor points to the parent Arbor
   ...     return data["mass"] / data["virial_radius"]
   ...
   >>> a.add_derived_field("potential", potential_field, units="Msun/Mpc")
   [  2.88624262e+14   2.49542426e+14   2.46280488e+14, ...
   3.47503685e+12   3.47503685e+12   3.47503685e+12] Msun/Mpc

Field functions should take two arguments. The first is a dictionary
that will contain basic information about the field, such as its name.
The second argument represents the data container for which the field
will be defined. It can be used to access field data for any other
available field. This argument will also have access to the parent
:class:`~ytree.data_structures.arbor.Arbor` as ``data.arbor``.

.. _vector-fields:

Vector Fields
-------------

For fields that have x, y, and z components, such as position, velocity,
and angular momentum, a single field can be queried to return an array
with all the components. For example, for fields named "position_x",
"position_y", and "position_z", the field "position" will return the
full vector.

.. code-block:: python

   >>> print (a["position"])
   [[0.0440018, 0.0672202, 0.9569643],
    [0.7383264, 0.1961563, 0.0238852],
    [0.7042797, 0.6165487, 0.500576 ],
    ...
    [0.1822363, 0.1324423, 0.1722414],
    [0.8649974, 0.4718005, 0.7349876]]) unitary

A list of defined vector fields can be seen by doing:

.. code-block:: python

   >>> print (a.field_info.vector_fields)
   ('position', 'velocity', 'angular_momentum')

For all vector fields, a "_magnitude" field also exists, defined as the
quadrature sum of the components.

.. code-block:: python

   >>> print (a["velocity_magnitude"])
   [ 488.26936644  121.97143067  146.81450507, ...
     200.74057711  166.13782652  529.7336846 ] km/s

Only specifically registered fields will be available as vector fields.
For example, saved :ref:`analysis-fields` with x,y,z components will
not automatically be available. However, vector fields can be created
with the :func:`~ytree.data_structures.arbor.Arbor.add_vector_field`
function.

.. code-block:: python

   >>> a.add_vector_field("thing")

The above example assumes that fields named "thing_x", "thing_y",
and "thing_z" already exist.

.. _analysis-fields:

Analysis Fields
---------------

Analysis fields provide a means for saving the results of complicated
analysis for any halo in the :class:`~ytree.data_structures.arbor.Arbor`.
This would be operations beyond derived fields, for example, things that
might require loading the original simulation snapshots. New analysis
fields are created with
:func:`~ytree.data_structures.arbor.Arbor.add_analysis_field` and are
initialized to zero.

.. code-block:: python

   >>> a.add_analysis_field("saucer_sections", units="m**2")
   >>> my_tree = a[0]
   >>> print (my_tree["tree", "saucer_sections"])
   [ 0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
     0.,  0.,] m**2
   >>> import numpy as np
   >>> for halo in my_tree["tree"]:
   ...     halo["saucer_sections"] = np.random.random() # complicated analysis
   ...
   >>> print (my_tree["tree", "saucer_sections"])
   [ 0.33919263  0.79557815  0.38264336  0.53073945  0.09634924  0.6035886, ...
     0.9506636   0.9094426   0.85436984  0.66779632  0.58816873] m**2

Analysis fields will be saved when the
:class:`~ytree.data_structures.tree_node.TreeNode` objects that have been
analyzed are saved with :func:`~ytree.data_structures.arbor.Arbor.save_arbor`
or :func:`~ytree.data_structures.tree_node.TreeNode.save_tree`.

.. code-block:: python

   >>> my_trees = list(a[:]) # all trees
   >>> for my_tree in my_trees:
   ...     # do analysis...
   >>> a.save_arbor(trees=my_trees)

Note that we do ``my_trees = list(a[:])`` and not just ``my_trees =
a[:]``. This is because ``a[:]`` is a generator that will return a new
set of trees each time. The newly generated trees will not retain
changes made to any analysis fields. Thus, we must use ``list(a[:])``
to explicitly store a list of trees.

Re-saving Analysis Fields
^^^^^^^^^^^^^^^^^^^^^^^^^

All analysis fields are saved to sidecar files with the "-analysis" keyword
appended to them. They can be altered and the arbor re-saved as many times
as you like. In the very specific case of re-saving all trees and not
providing a new filename or custom list of fields (as in the example above),
analysis fields will be saved in place (i.e., over-writing the "-analysis"
files). The conventional on-disk fields will not be re-saved as they cannot
be altered.
