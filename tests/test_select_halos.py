"""
tests for select_halos function



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from numpy.testing import assert_raises

import ytree

from ytree.utilities.exceptions import ArborFieldNotFound
from ytree.testing.utilities import requires_file

CT = "consistent_trees/tree_0_0_0.dat"


@requires_file(CT)
def test_select_halos():
    a = ytree.load(CT)

    halos = a.select_halos('tree["tree", "Orig_halo_ID"] == 0')
    hids = a.arr([h["Orig_halo_ID"] for h in halos])
    assert (hids == 0).all()

    halos = a.select_halos('tree["prog", "Orig_halo_ID"] == 0')
    hids = a.arr([h["Orig_halo_ID"] for h in halos])
    assert (hids == 0).all()


@requires_file(CT)
def test_select_halos_bad_input():
    a = ytree.load(CT)

    with assert_raises(ArborFieldNotFound):
        list(a.select_halos("(tree['forest', 'not_a_field'].to('Msun') > 1e13)"))

    with assert_raises(ValueError):
        list(a.select_halos("(tree['flock', 'mass'].to('Msun') > 1e13)"))
        list(
            a.select_halos(
                "(tree['forest', 'mass'].to('Msun') > 1e13) & (tree['tree', 'redshift'] < 0.5)"
            )
        )
