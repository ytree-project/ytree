"""
test for documented examples



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from ytree.utilities.testing import \
    requires_file, \
    TempDirTest

import ytree

CTG = "tiny_ctrees/locations.dat"

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

class ExampleTest(TempDirTest):
    """
    Tests of the examples in the documentation
    """

    @requires_file(CTG)
    def test_halo_age(self):
        """
        Test halo age example.
        """

        a = ytree.load(CTG)
        my_tree = a[0]
        age = t50(my_tree).to('Gyr')
        print (age)

    @requires_file(CTG)
    def test_significance(self):
        """
        Test John Wise's significance.
        """

        a = ytree.load(CTG)
        a.add_analysis_field('significance', 'Msun*Myr')
        my_trees = list(a[:])
        for tree in my_trees:
            get_significance(tree)

        fn = a.save_arbor(filename='sig_tree', trees=my_trees)
        a2 = ytree.load(fn)
        a2.set_selector('max_field_value', 'significance')
        prog = a2[0]['prog']
        print (prog)
