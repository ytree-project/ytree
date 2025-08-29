"""
tests for derived fields



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import numpy as np
from numpy.testing import assert_array_equal, assert_equal

from ytree.testing.utilities import requires_file, TempDirTest

import ytree

CT = "consistent_trees/tree_0_0_0.dat"


def _potential(field, data):
    return data["mass"] / data["virial_radius"]


def _uid_mod7(field, data):
    return data["uid"] % 7


class DerivedFieldTest(TempDirTest):
    @requires_file(CT)
    def test_derived_fields(self):
        a = ytree.load(CT)

        a.add_derived_field("potential", _potential, units="Msun/kpc")

        m = a["mass"].copy()
        r = a["virial_radius"].copy()
        assert_array_equal(a["potential"], m / r)
        assert_equal(str(a["potential"].units), "Msun/kpc")
        assert_equal(a["potential"].dtype, a._default_dtype)

        my_tree = a[0]
        m = my_tree["mass"].copy()
        r = my_tree["virial_radius"].copy()
        assert_array_equal(my_tree["potential"], m / r)
        assert_equal(str(my_tree["potential"].units), "Msun/kpc")
        assert_equal(my_tree["potential"].dtype, a._default_dtype)

    @requires_file(CT)
    def test_derived_fields_int(self):
        a = ytree.load(CT)

        my_dtype = np.int64
        a.add_derived_field("uid_mod7", _uid_mod7, units="", dtype=my_dtype)

        um7 = a["uid"] % 7
        assert_array_equal(a["uid_mod7"], um7)
        assert_equal(a["uid_mod7"].dtype, my_dtype)

        my_tree = a[0]
        um7 = my_tree["tree", "uid"] % 7
        assert_array_equal(my_tree["tree", "uid_mod7"], um7)
        assert_equal(my_tree["tree", "uid_mod7"].dtype, my_dtype)
