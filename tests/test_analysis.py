"""
tests for analysis fields



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
from numpy.testing import \
    assert_array_equal, \
    assert_equal
import os

from ytree.utilities.testing import \
    requires_file, \
    test_data_dir, \
    TempDirTest

import ytree

CT = os.path.join(test_data_dir,
                  "consistent_trees/tree_0_0_0.dat")

class AnalysisFieldTest(TempDirTest):
    @requires_file(CT)
    def test_analysis_fields(self):
        a = ytree.load(CT)

        a.add_analysis_field('bears', 'Msun/yr')
        assert_equal(a._default_dtype, a['bears'].dtype)

        fake_bears = np.zeros(a.size)
        assert_array_equal(fake_bears, a['bears'])

        all_trees = a[:]
        my_tree = all_trees[0]
        my_tree['bears'] = 9
        fake_bears[0] = 9
        assert_array_equal(fake_bears, a['bears'])

        my_tree = all_trees[1]
        assert_equal(a._default_dtype, my_tree['tree', 'bears'].dtype)
        fake_tree_bears = np.zeros(my_tree.tree_size)
        assert_array_equal(
            fake_tree_bears, my_tree['tree', 'bears'])
        fake_tree_bears[72] = 99
        my_tree['tree'][72]['bears'] = 99
        assert_array_equal(fake_tree_bears, my_tree['tree', 'bears'])

        fn = a.save_arbor(trees=all_trees)
        a2 = ytree.load(fn)

        assert_array_equal(fake_bears, a2['bears'])
        assert_array_equal(fake_tree_bears, a2[1]['tree', 'bears'])
        assert_equal(a2['bears'].dtype, a._default_dtype)
        assert_equal(a2[1]['tree', 'bears'].dtype, a._default_dtype)

    @requires_file(CT)
    def test_analysis_fields_int(self):
        a = ytree.load(CT)

        my_dtype = np.int64
        a.add_analysis_field('bears', 'Msun/yr', dtype=my_dtype)
        assert_equal(my_dtype, a['bears'].dtype)

        fake_bears = np.zeros(a.size)
        assert_array_equal(fake_bears, a['bears'])

        all_trees = a[:]
        my_tree = all_trees[0]
        my_tree['bears'] = 9
        fake_bears[0] = 9
        assert_array_equal(fake_bears, a['bears'])

        my_tree = all_trees[1]
        assert_equal(my_dtype, my_tree['tree', 'bears'].dtype)
        fake_tree_bears = np.zeros(my_tree.tree_size)
        assert_array_equal(
            fake_tree_bears, my_tree['tree', 'bears'])
        fake_tree_bears[72] = 99
        my_tree['tree'][72]['bears'] = 99
        assert_array_equal(fake_tree_bears, my_tree['tree', 'bears'])

        fn = a.save_arbor(trees=all_trees)
        a2 = ytree.load(fn)

        assert_array_equal(fake_bears, a2['bears'])
        assert_array_equal(fake_tree_bears, a2[1]['tree', 'bears'])
        assert_equal(a2['bears'].dtype, my_dtype)
        assert_equal(a2[1]['tree', 'bears'].dtype, my_dtype)
