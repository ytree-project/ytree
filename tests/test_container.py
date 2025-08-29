"""
tests for NodeContainer



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import numpy as np
from numpy.testing import assert_array_equal

import ytree

from ytree.testing.utilities import requires_file

TCL = "tiny_ctrees/locations.dat"


@requires_file(TCL)
def test_containers():
    a = ytree.load(TCL)

    first = a[0]
    last = a[-1]
    container = a.container([first, last])
    masses = a.arr([node["mass"] for node in [first, last]])
    assert_array_equal(container["mass"], masses)
    assert container.size == 2
    assert container.size == len(container)

    my_tree = a[0]
    leaves = my_tree.get_leaf_nodes()
    leaf_container = a.container(leaves)
    for i, leaf in enumerate(leaf_container):
        assert leaf["mass"] == leaf_container["mass"][i]

    a_slice = a.container(a[::8])
    assert int(np.ceil(a.size / 8)) == a_slice.size
    assert_array_equal(a_slice["mass"], a["mass"][::8])
