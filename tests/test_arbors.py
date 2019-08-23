"""
arbor tests



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from ytree.arbor.frontends.consistent_trees import \
    ConsistentTreesArbor
from ytree.arbor.frontends.ahf import \
    AHFArbor
from ytree.arbor.frontends.rockstar import \
    RockstarArbor
from ytree.arbor.frontends.treefarm import \
    TreeFarmArbor
from ytree.arbor.frontends.lhalotree import \
    LHaloTreeArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class AHFArborTest(TempDirTest, ArborTest):
    arbor_type = AHFArbor
    test_filename = "ahf_halos/snap_N64L16_000.parameter"

class ConsistentTreesArborTest(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesArbor
    test_filename = "consistent_trees/tree_0_0_0.dat"

class RockstarArborTest(TempDirTest, ArborTest):
    arbor_type = RockstarArbor
    test_filename = "rockstar/rockstar_halos/out_0.list"

class TreeFarmArborDescendentsTest(TempDirTest, ArborTest):
    arbor_type = TreeFarmArbor
    test_filename = "tree_farm/tree_farm_descendents/fof_subhalo_tab_000.0.h5"

class TreeFarmArborAncestorsTest(TempDirTest, ArborTest):
    arbor_type = TreeFarmArbor
    test_filename = "tree_farm/tree_farm_ancestors/fof_subhalo_tab_017.0.h5"

class LHaloTreeArborTest(TempDirTest, ArborTest):
    arbor_type = LHaloTreeArbor
    test_filename = "lhalotree/trees_063.0"
    tree_skip = 10
