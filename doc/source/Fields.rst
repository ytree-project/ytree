.. _fields:

Fields in ytree
===============

ytree supports multiple types of fields, each representing numerical
values associated with each halo in the ``Arbor``.  These include the
:ref:`native fields <native-fields>` stored on disk, :ref:`alias fields
<alias-fields>`, :ref:`derived fields <derived-fields>`, and
:ref:`analysis fields <analysis-fields>`.

The Field Info Container
------------------------

Each :class:`~ytree.arbor.arbor.Arbor` contains a dictionary,
called :func:`~ytree.arbor.arbor.Arbor.field_info`,
with relevant information for each available field.  This information
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
the ``Arbor``.  The ``field_list`` contains a list of all fields on disk
with their native names.

.. code-block:: python

   >>> print (a.field_list)
   ['scale', 'id', 'desc_scale', 'desc_id', 'num_prog', ...]

.. _alias-fields:

Alias Fields
------------

Because the various dataset formats use different naming conventions for
similar fields, ytree allows fields to be referred to by aliases.  This
allows for a universal set of names for the most common fields.  Many are
added by default, including "mass", "virial_radius", "position_<xyz>",
and "velocity_<xyz>".  The list of available alias and derived fields
can be found in the ``derived_field_list``.

.. code-block:: python

   print (a.derived_field_list)
   ['uid', 'desc_uid', 'scale_factor', 'mass', 'virial_mass', ...]

Additional aliases can be added with
:func:`~ytree.arbor.arbor.Arbor.add_alias_field`.

.. code-block:: python

   >>> a.add_alias_field("amount_of_stuff", "mass", units="kg")
   >>> print (a["amount_of_stuff"])
   [  1.30720461e+45,   1.05085632e+45,   1.03025691e+45, ...
   1.72691772e+42,   1.72691772e+42,   1.72691772e+42]) kg

.. _derived-fields:

Derived Fields
--------------

Derived fields are functions of existing fields, including other
derived and alias fields.  New derived fields are created by
providing a defining function and calling
:func:`~ytree.arbor.arbor.Arbor.add_derived_field`.

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
available field.  This argument will also have access to the parent
``Arbor`` as ``data.arbor``.

.. _analysis-fields:

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

Analysis Fields
---------------

Analysis fields provide a means for saving the results of complicated
analysis for any halo in the ``Arbor``.  This would be operations
beyond derived fields, for example, things that might require loading
the original simulation snapshots.  New analysis fields are created
with :func:`~ytree.arbor.arbor.Arbor.add_analysis_field` and are
initialized to zero.

.. code-block:: python

   >>> a.add_analysis_field("saucer_sections", units="m**2")
   >>> print (a[0]["tree", "saucer_sections"])
   [ 0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
     0.,  0.,] m**2
   >>> import numpy as np
   >>> for t in a[0]["tree"]:
   ...     t["saucer_sections"] = np.random.random() # complicated analysis
   ...
   >>> print (a[0]["tree", "saucer_sections"])
   [ 0.33919263  0.79557815  0.38264336  0.53073945  0.09634924  0.6035886, ...
     0.9506636   0.9094426   0.85436984  0.66779632  0.58816873] m**2

Analysis fields will be automatically saved when the ``Arbor`` is saved
with :func:`~ytree.arbor.arbor.Arbor.save_arbor`.
