.. _plotting:

Plotting Merger Trees
=====================

Some relatively simple visualizations of merger trees can be made with
the :class:`~ytree.visualization.tree_plot.TreePlot` command.

Additional Dependencies
-----------------------

Making merger tree plots with ``ytree`` requires the
`pydot <https://pypi.org/project/pydot/>`__ and
`graphviz <https://www.graphviz.org/>`__ packages. ``pydot`` can be
installed with ``pip`` and the
`graphviz <https://www.graphviz.org/>`__ website provides a number
of installation options.

Making Tree Plots
-----------------

The :class:`~ytree.visualization.tree_plot.TreePlot` command can be
used to create a `digraph <https://en.wikipedia.org/wiki/Directed_graph>`__
depicting halos as filled circles with sizes proportional to their mass.
The main progenitor line will be colored red.

.. code-block:: python

    >>> import ytree
    >>> a = ytree.load("ahf_halos/snap_N64L16_000.parameter",
    ...                hubble_constant=0.7)
    >>> p = ytree.TreePlot(a[0], dot_kwargs={'rankdir': 'LR', 'size': '"12,4"'})
    >>> p.save('tree.png')

.. image:: _images/tree.png

Plot Modifications
^^^^^^^^^^^^^^^^^^

Four :class:`~ytree.visualization.tree_plot.TreePlot` attributes can be set
to modify the default plotting behavior. These are:

- *size_field*: The field to determine the size of each circle. Default:
  'mass'.

- *size_log*: Whether to scale circle sizes based on log of size field.
  Default: True.

- *min_mass*: The minimum halo mass to be included in the plot. If given
  as a float, units are assumed to be Msun. Default: None.

- *min_mass_ratio*: The minimum ratio between a halo's mass and the mass
  of the main halo to be included in the plot. Default: None.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("ahf_halos/snap_N64L16_000.parameter",
   ...                hubble_constant=0.7)
   >>> p = ytree.TreePlot(a[0], dot_kwargs={'rankdir': 'LR', 'size': '"12,4"'})
   >>> p.min_mass_ratio = 0.01
   >>> p.save('tree_small.png')

.. image:: _images/tree_small.png

Supported Output Formats
^^^^^^^^^^^^^^^^^^^^^^^^

Plots can be saved to any format supported by ``graphviz`` by giving a
filename with the appropriate extension. See
`here <https://www.graphviz.org/doc/info/output.html>`__ for a list of
currently supported formats.
