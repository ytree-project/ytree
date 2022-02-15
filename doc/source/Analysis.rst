.. _analysis:

Analyzing Merger Trees
======================

This section describes the preferred method for performing analysis
on merger trees that results in modification of the dataset (e.g., by
creating or altering :ref:`analysis-fields`) or writing additional
files. The end of this section, :ref:`parallel_analysis`, illustrates
an analysis workflow that will run in parallel.

When performing the same analysis on a large number of items, we often
think in terms of creating an "analysis pipeline", where a series of
discrete actions, including deciding whether to skip a given item, are
embedded within a loop over all the items to analyze. For merger
trees, this may look something like the following:

.. code-block:: python

   import ytree

   a = ytree.load(...)

   trees = list(a[:])
   for tree in trees:
       for node in tree["forest"]:

           # only analyze above some minimum mass
           if node["mass"] < a.quan(1e11, "Msun"):
               continue

           # get simulation snapshot associated with this halo
           snap_fn = get_filename_from_redshift(node["redshift"])
           ds = yt.load(snap_fn)

           # get sphere using halo's center and radius
           center = node["position"].to("unitary")
           radius = node["virial_radius"].to("unitary")
           sp = ds.sphere((center, "unitary"), (radius, "unitary"))

           # calculate gas mass and save to field
           node["gas_mass"] = sp.quantities.total_quantity(("gas", "mass"))

           # make a projection and save an image
           p = yt.ProjectionPlot(ds, "x", ("gas", "density"),
                                 data_source=sp, center=sp.center,
                                 width=2*sp.width)
           p.save("my_analysis/projections/")

There are a few disadvantages of this approach. The inner loop is very
long. It can be difficult to understand the full set of actions,
especially if you weren't the one who wrote it. If there is a section
you no longer want to do, a whole block of code needs to be commented
out or removed, and it may be tricky to tell if doing that will break
something else. Putting the operations into functions will make this
simpler, but it can still make for a large code block in the inner
loop. As well, if the structure of the loops over trees or nodes is
more complicated than the above, there is potential for the code to be
non-trivial to digest.

.. _analysis_pipeline:

The AnalysisPipeline
--------------------

The :class:`~ytree.analysis.analysis_pipeline.AnalysisPipeline` allows
you to design the analysis workflow in advance and then use it to
process a tree or node with a single function call. Skipping straight
to the end, the loop from above will take the form:

.. code-block:: python

   for tree in trees:
       for node in tree["forest"]:
           ap.process_target(node)

In the above example, "ap" is some
:class:`~ytree.analysis.analysis_pipeline.AnalysisPipeline` object
that we have defined earlier. We will now take a closer look at how to
design a workflow using this method.

Creating an AnalysisPipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An :class:`~ytree.analysis.analysis_pipeline.AnalysisPipeline` is
instantiated with no arguments. Only an optional output directory
inside which new files will be written can be specified with the
``output_dir`` keyword.

.. code-block:: python

   import ytree

   ap = ytree.AnalysisPipeline(output_dir="my_analysis")

The output directory will be created automatically if it does not
already exist.

Creating Pipeline Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An analysis pipeline is assembled by creating functions that accept a
single :class:`~ytree.data_structures.tree_node.TreeNode` as an
argument.

.. code-block:: python

   def say_hello(node):
       print (f"This is node {node}! I will now be analyzed.")

This function can now be added to an existing pipeline with the
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.add_operation`
function.

.. code-block:: python

   ap.add_operation(say_hello)

Now, when the
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.process_target`
function is called with a
:class:`~ytree.data_structures.tree_node.TreeNode` object, the
``say_hello`` function will be called with that
:class:`~ytree.data_structures.tree_node.TreeNode`. Any additional
calls to
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.add_operation`
will result in those functions also being called with that
:class:`~ytree.data_structures.tree_node.TreeNode` in the same order.

Adding Extra Function Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Functions can take additional arguments and keyword arguments as
well.

.. code-block:: python

   def print_field_value(node, field, units=None):
       val = node[field]
       if units is not None:
           val.convert_to_units(units)
       print (f"Value of {field} for node {node} is {val}.")

The additional arguments and keyword arguments are then provided when
calling
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.add_operation`.

.. code-block:: python

   ap.add_operation(print_field_value, "mass")
   ap.add_operation(print_field_value, "virial_radius", units="kpc/h")

Organizing File Output by Operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the same way that the
:class:`~ytree.analysis.analysis_pipeline.AnalysisPipeline` object
accepts an ``output_dir`` keyword, analysis functions can also accept
an ``output_dir`` keyword.

.. code-block:: python

   def save_something(node, output_dir=None):
       # make an HDF5 file named by the unique node ID
       filename = f"node_{node.uid}.h5"
       if output_dir is not None:
           filename = os.path.join(output_dir, filename)

       # do some stuff...

   # meanwhile, back in the pipeline...
   ap.add_operation(save_something, output_dir="images")

This ``output_dir`` keyword will be intercepted by the
:class:`~ytree.analysis.analysis_pipeline.AnalysisPipeline` object to
ensure that the directory gets created if it does not already
exist. Additionally, if an ``output_dir`` keyword was given when the
:class:`~ytree.analysis.analysis_pipeline.AnalysisPipeline` was
created, as in the example above, the directory associated with the
function will be appended to that. Following the examples here, the
resulting directory would be "my_analysis/images", and the code above
will correctly save to that location.

.. _operation-as-filter:

Using a Function as a Filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Making an analysis function return ``True`` or ``False`` allows it to
act as a filter. If a function returns ``False``, then any
additional operations defined in the pipeline will not be
performed. For example, we might create a mass filter like this:

.. code-block:: python

   def minimum_mass(node, value):
       return node["mass"] >= value

   # later, in the pipeline
   ap.add_operation(minimum_mass, a.quan(1e11, "Msun"))

The pipeline will interpret any return value from an operation that is
not ``None`` in a boolean context to use as a filter.

.. _operation-always-do:

Adding Operations that Always Run
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As discussed above in :ref:`operation-as-filter`, returning ``False``
from an operation will prevent all further operations in the pipeline
from being performed on that node. However, there may be operations
that you want to always run, regardless of previous filters. For
example, there may be clean up operations, like freeing up memory,
that should run for every node, no matter what. To accomplish this,
the ``always_do`` keyword can be set to ``True`` in the call to
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.add_operation`.

.. code-block:: python

   def delete_attributes(node, attributes):
       for attr in attributes:
           if hasattr(node, attr):
               delattr(node, attr)

   # later, in the pipeline
   ap.add_operation(delete_attributes, ["ds", "sphere"], always_do=True)

Modifying a Node
^^^^^^^^^^^^^^^^

There may be occasions where you want to pass local variables or
objects around from one function to the next. The easiest way to do
this is by attaching them to the
:class:`~ytree.data_structures.tree_node.TreeNode` object itself as an
attribute. For example, say we have a function that returns a
simulation snapshot loaded with ``yt`` as a function of redshift. We
might do something like the the following to then pass it to another
function which creates a ``yt`` sphere.

.. code-block:: python

   def get_yt_dataset(node):
       # assume you have something like this
       filename = get_filename_from_redshift(node["redshift"])
       # attach it to the node for later use
       node.ds = yt.load(filename)

   def get_yt_sphere(node):
       # this works if get_yt_dataset has been called first
       ds = node.ds
       
       center = node["position"].to("unitary")
       radius = node["virial_radius"].to("unitary")
       node.sphere = ds.sphere((center, "unitary"), (radius, "unitary"))

Then, we can add these to the pipeline such that a later function can
use the sphere.

.. code-block:: python

   ap.add_operation(get_yt_dataset)
   ap.add_operation(get_yt_sphere)

To clean things up, we can make a function to remove attributes and
add it to the end of the pipeline.

.. code-block:: python

   def delete_attributes(node, attributes):
       for attr in attributes:
           if hasattr(node, attr):
               delattr(node, attr)

   # later, in the pipeline
   ap.add_operation(delete_attributes, ["ds", "sphere"], always_do=True)

See :ref:`operation-always-do` for a discussion of the ``always_do``
option.

Running the Pipeline
^^^^^^^^^^^^^^^^^^^^

Once the pipeline has been defined through calls to
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.add_operation`,
it is now only a matter of looping over the nodes we want to analyze
and calling
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.process_target`
with them.

.. code-block:: python

   for tree in trees:
       for node in tree["forest"]:
           ap.process_target(node)

Depending on what you want to do, you may want to call
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.process_target`
with an entire tree and skip the inner loop. After all, a tree in this
context is just another
:class:`~ytree.data_structures.tree_node.TreeNode` object, only one
that has no descendent.

Creating a Analysis Recipe
^^^^^^^^^^^^^^^^^^^^^^^^^^

Through the previous examples, we have designed a workflow by defining
functions and adding them to our pipeline in the order we want them to
be called. Has it resulted in fewer lines of code? No. But it has
allowed us to construct a workflow out of a series of reusable parts,
so the creation of future pipelines will certainly involve fewer lines
of code. It is also possible to define a more complex series of
operations as a "recipe" that can be added in one go to the pipeline
using the
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.add_recipe`
function. A recipe should be a function that, minimally, accepts an
:class:`~ytree.analysis.analysis_pipeline.AnalysisPipeline` object as
the first argument, but can also accept more. Below, we will define a
recipe for calculating the gas mass for a halo. For our purposes,
assume the functions we created earlier exist here.

.. code-block:: python

   def calculate_gas_mass(node):
       sphere = node.sphere
       node["gas_mass"] = sphere.quantities.total_quantity(("gas", "mass"))

   def gas_mass_recipe(pipeline):
       pipeline.add_operation(get_yt_dataset)
       pipeline.add_operation(get_yt_sphere)
       pipeline.add_operation(calculate_gas_mass)
       pipeline.add_operation(delete_attributes, ["ds", "sphere"])

Now, our entire analysis pipeline design can look like this.

.. code-block:: python

      ap = ytree.AnalysisPipeline()
      ap.add_recipe(gas_mass_recipe)

See the
:func:`~ytree.analysis.analysis_pipeline.AnalysisPipeline.add_recipe`
docstring for an example of including additional function arguments.

.. _parallel_analysis:

Putting it all Together: Parallel Analysis
------------------------------------------

To unleash the true power of the
:class:`~ytree.analysis.analysis_pipeline.AnalysisPipeline`, run it in
parallel using one of the :ref:`parallel_iterators`. See
:ref:`ytree_parallel` for more information on using ``ytree`` on
multiple processors.

.. code-block:: python

   import ytree

   a = ytree.load("arbor/arbor.h5")
   if "test_field" not in a.field_list:
       a.add_analysis_field("gas_mass", default=-1, units="Msun")

   ap = ytree.AnalysisPipeline()
   ap.add_recipe(gas_mass_recipe)

   trees = list(a[:])
   for node in ytree.parallel_nodes(trees):
       ap.process_target(node)

If you need some inspiration, have a look at some :ref:`examples`.
