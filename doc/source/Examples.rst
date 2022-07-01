.. _examples:

Example Applications
====================

Below are some examples of things one might want to do with merger
trees that demonstrate various ``ytree`` functions. If you have made
something interesting, please add it!

Halo Age (a50)
--------------

One way to define the age of a halo is by calculating the scale factor
when it reached 50% of its current mass. This is often referred to as
"a50". In the example below, this is calculated by linearly
interpolating from the mass of the main progenitor.

.. code-block:: python

   import numpy as np

   def calc_a50(node):
       # main progenitor masses
       pmass = node["prog", "mass"]

       mh = 0.5 * node["mass"]
       m50 = pmass <= mh

       if not m50.any():
           ah = node["scale_factor"]
       else:
           pscale = node["prog", "scale_factor"]
           # linearly interpolate
           i = np.where(m50)[0][0]
           slope = (pscale[i-1] - pscale[i]) / (pmass[i-1] - pmass[i])
           ah = slope * (mh - pmass[i]) + pscale[i]

       node["a50"] = ah

Now we'll run it using the :ref:`analysis_pipeline`.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load("consistent_trees/tree_0_0_0.dat")
   >>> a.add_analysis_field("a50", "")

   >>> ap = ytree.AnalysisPipeline()
   >>> ap.add_operation(calc_a50)

   >>> trees = list(a[:])
   >>> for tree in trees:
   ...     ap.process_target(tree)

   >>> fn = a.save_arbor(filename="halo_age", trees=trees)
   >>> a2 = ytree.load(fn)
   >>> print (a2[0]["a50"])
   0.57977664

Significance
------------

Brought to you by John Wise, a halo's significance is calculated by
recursively summing over all ancestors the mass multiplied by the time
between snapshots. When determining the main progenitor of a halo, the
significance measure will select for the ancestor with the deeper
history instead of just the higher mass. This can be helpful in cases
of near 1:1 mergers.

Below, we define a function that calculates the significance
for every halo in a single tree.

.. code-block:: python

   def calc_significance(node):
      if node.descendent is None:
          dt = 0. * node["time"]
      else:
          dt = node.descendent["time"] - node["time"]

      sig = node["mass"] * dt
      if node.ancestors is not None:
          for anc in node.ancestors:
              sig += calc_significance(anc)

      node["significance"] = sig
      return sig

Now, we'll use the :ref:`analysis_pipeline` to calculate the
significance for all trees and save a new dataset. After loading the
new arbor, we use the
:func:`~ytree.data_structures.arbor.Arbor.set_selector` function to
use the new significance field to determine the progenitor line.

.. code-block:: python

   >>> a = ytree.load("tiny_ctrees/locations.dat")
   >>> a.add_analysis_field("significance", "Msun*Myr")

   >>> ap = ytree.AnalysisPipeline()
   >>> ap.add_operation(calc_significance)

   >>> trees = list(a[:])
   >>> for tree in trees:
   ...     ap.process_target(tree)

   >>> fn = a.save_arbor(filename="significance", trees=trees)
   >>> a2 = ytree.load(fn)
   >>> a2.set_selector("max_field_value", "significance")
   >>> prog = list(a2[0]["prog"])
   >>> print (prog)
   [TreeNode[1457223360], TreeNode[1452164856], TreeNode[1447024182], ...
    TreeNode[6063823], TreeNode[5544219], TreeNode[5057761]]