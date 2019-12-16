.. _examples:

Example Applications
====================

Below are some examples of things one might want to do with merger
trees that demonstrate various ``ytree`` functions. If you have made
something interesting, please consider contributing it.

Halo Age
--------

One way to define the age of a halo is by calculating the time
when it reached 50% of its current mass. In the example below,
this time is calculated by linearly interpolating from the mass
of the main progenitor as a function of time.

.. code-block:: python

    import numpy as np

    def t50(tree):
        # main progenitor masses
        pmass = tree['prog', 'mass']

        mh = 0.5 * tree['mass']
        m50 = pmass <= mh

        if not m50.any():
            th = tree['time']
        else:
            ptime = tree['prog', 'time']
            # linearly interpolate
            i = np.where(m50)[0][0]
            slope = (ptime[i-1] - ptime[i]) / (pmass[i-1] - pmass[i])
            th = slope * (mh - pmass[i]) + ptime[i]

        return th

Now we'll run it on the first tree in the data set.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load('consistent_trees/tree_0_0_0.dat')
   >>> my_tree = a[0]
   >>> print (t50(my_tree).to('Gyr'))
   7.2325572094782515 Gyr

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

   def get_significance(tree):
       if tree.descendent is None:
           dt = 0. * tree['time']
       else:
           dt = tree.descendent['time'] - tree['time']

       sig = tree['mass'] * dt
       if tree.ancestors is not None:
           for anc in tree.ancestors:
               sig += get_significance(anc)

       tree['significance'] = sig
       return sig

We now add a new analysis field to save the significance values
for all trees. Then, we will save the arbor with the newly added
significance field.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load('consistent_trees/tree_0_0_0.dat')
   >>> a.add_analysis_field('significance', 'Msun*Myr')
   >>> for tree in a:
           get_significance(tree)
   >>> a.save_arbor('sig_tree')

Finally, we can load the new data set and use the significance
field to select the main progenitors.

.. code-block:: python

   >>> import ytree
   >>> a = ytree.load('sig_tree/sig_tree.h5')
   >>> a.set_selector('max_field_value', 'significance')
   >>> print (a[0]['prog'])
   [TreeNode[12900] TreeNode[12539] TreeNode[12166] TreeNode[11796] ...
    TreeNode[105] TreeNode[62]]
 