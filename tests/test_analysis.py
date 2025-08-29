"""
tests for analysis fields



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import numpy as np
from numpy.testing import assert_array_equal, assert_equal, assert_raises

from ytree.utilities.exceptions import ArborFieldAlreadyExists, ArborUnsettableField
from ytree.testing.utilities import requires_file, TempDirTest

import ytree

CT = "consistent_trees/tree_0_0_0.dat"


class AnalysisFieldTest(TempDirTest):
    @requires_file(CT)
    def test_analysis_fields(self):
        a = ytree.load(CT)

        a.add_analysis_field("bears", "Msun/yr")
        assert_equal(a._default_dtype, a["bears"].dtype)

        fake_bears = np.zeros(a.size)
        assert_array_equal(fake_bears, a["bears"])

        all_trees = list(a[:])
        my_tree = all_trees[0]
        my_tree["bears"] = 9
        fake_bears[0] = 9
        assert_array_equal(fake_bears, a["bears"])

        my_tree = all_trees[1]
        assert_equal(a._default_dtype, my_tree["tree", "bears"].dtype)
        fake_tree_bears = np.zeros(my_tree.tree_size)
        assert_array_equal(fake_tree_bears, my_tree["tree", "bears"])
        fake_tree_bears[72] = 99
        my_halos = list(my_tree["tree"])
        my_halos[72]["bears"] = 99
        assert_array_equal(fake_tree_bears, my_tree["tree", "bears"])

        fn = a.save_arbor(trees=all_trees)
        a2 = ytree.load(fn)

        assert_array_equal(fake_bears, a2["bears"])
        assert_array_equal(fake_tree_bears, a2[1]["tree", "bears"])
        assert_equal(a2["bears"].dtype, a._default_dtype)
        assert_equal(a2[1]["tree", "bears"].dtype, a._default_dtype)

    @requires_file(CT)
    def test_analysis_fields_int(self):
        a = ytree.load(CT)

        my_dtype = np.int64
        a.add_analysis_field("bears", "Msun/yr", dtype=my_dtype)
        assert_equal(my_dtype, a["bears"].dtype)

        fake_bears = np.zeros(a.size)
        assert_array_equal(fake_bears, a["bears"])

        all_trees = list(a[:])
        my_tree = all_trees[0]
        my_tree["bears"] = 9
        fake_bears[0] = 9
        assert_array_equal(fake_bears, a["bears"])

        my_tree = all_trees[1]
        assert_equal(my_dtype, my_tree["tree", "bears"].dtype)
        fake_tree_bears = np.zeros(my_tree.tree_size)
        assert_array_equal(fake_tree_bears, my_tree["tree", "bears"])
        fake_tree_bears[72] = 99
        my_halos = list(my_tree["tree"])
        my_halos[72]["bears"] = 99
        assert_array_equal(fake_tree_bears, my_tree["tree", "bears"])

        fn = a.save_arbor(trees=all_trees)
        a2 = ytree.load(fn)

        assert_array_equal(fake_bears, a2["bears"])
        assert_array_equal(fake_tree_bears, a2[1]["tree", "bears"])
        assert_equal(a2["bears"].dtype, my_dtype)
        assert_equal(a2[1]["tree", "bears"].dtype, my_dtype)

    @requires_file(CT)
    def test_analysis_field_already_exists(self):
        a = ytree.load(CT)

        with assert_raises(ArborFieldAlreadyExists):
            a.add_analysis_field("mass", units="g")

    @requires_file(CT)
    def test_analysis_unsettable_fields(self):
        a = ytree.load(CT)

        with assert_raises(ArborUnsettableField):
            my_tree = a[0]
            my_tree["mass"] = 50

    @requires_file(CT)
    def test_add_vector_field(self):
        a = ytree.load(CT)

        data = []
        for i, ax in enumerate("xyz"):
            a.add_analysis_field(f"thing_{ax}", "", default=i, dtype=np.float64)
            data.append(i * np.ones(a.size, dtype=np.float64))
        data = np.rollaxis(np.vstack(data), 1)

        fn = a.save_arbor()
        a2 = ytree.load(fn)
        a2.add_vector_field("thing")

        assert_array_equal(a2["thing"], data)

        data_mag = np.sqrt((data**2).sum(axis=1))
        assert_array_equal(a2["thing_magnitude"], data_mag)

    @requires_file(CT)
    def test_alter_vector_field(self):
        a = ytree.load(CT)

        for i, ax in enumerate("xyz"):
            a.add_analysis_field(f"thing_{ax}", "", default=i, dtype=np.float64)

        fn = a.save_arbor()
        a2 = ytree.load(fn)
        a2.add_vector_field("thing")

        t = a2[0]
        for i, ax in enumerate("xyz"):
            t[f"thing_{ax}"] += 1
            assert_array_equal(t["forest", f"thing_{ax}"], t["forest", "thing"][:, i])
            assert_array_equal(a2[f"thing_{ax}"], a2["thing"][:, i])

    @requires_file(CT)
    def test_reload_arbor(self):
        a = ytree.load(CT)

        fn = a.save_arbor()
        a = ytree.load(fn)
        a.add_analysis_field("bears", "Msun/yr")

        trees = list(a[:])
        a.save_arbor(trees=trees, save_in_place=True)

        a = a.reload_arbor()
        assert "bears" in a.field_list
