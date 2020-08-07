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

from ytree.frontends.ahf import \
    AHFArbor
from ytree.frontends.consistent_trees import \
    ConsistentTreesGroupArbor, \
    ConsistentTreesArbor, \
    ConsistentTreesHlistArbor
from ytree.frontends.consistent_trees_hdf5 import \
    ConsistentTreesHDF5Arbor
from ytree.frontends.lhalotree import \
    LHaloTreeArbor
from ytree.frontends.rockstar import \
    RockstarArbor
from ytree.frontends.treefarm import \
    TreeFarmArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class AHFArborTest(TempDirTest, ArborTest):
    arbor_type = AHFArbor
    test_filename = "ahf_halos/snap_N64L16_000.parameter"
    num_data_files = 136

class ConsistentTreesArborTest(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesArbor
    test_filename = "consistent_trees/tree_0_0_0.dat"
    num_data_files = 1

class ConsistentTreesGroupArborTest(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesGroupArbor
    test_filename = "tiny_ctrees/locations.dat"
    num_data_files = 8

    def test_data_files(self):
        self.arbor._plant_trees()
        ArborTest.test_data_files(self)

class ConsistentTreesHlistArborTest(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesHlistArbor
    test_filename = "ctrees_hlists/hlists/hlist_0.12521.list"
    num_data_files = 10
    tree_skip = 100

class ConsistentTreesHDF5ArborTest1(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesHDF5Arbor
    test_filename = "consistent_trees_hdf5/soa/forest.h5"
    num_data_files = 1
    tree_skip = 10000

class ConsistentTreesHDF5ArborTest2(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesHDF5Arbor
    test_filename = "consistent_trees_hdf5/soa/forest.h5"
    load_kwargs = {"access": "forest"}
    groups = ("forest", "tree", "prog")
    num_data_files = 1
    tree_skip = 10000

class ConsistentTreesHDF5ArborTest3(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesHDF5Arbor
    test_filename = "consistent_trees_hdf5/soa/forest_0.h5"
    num_data_files = 1
    tree_skip = 10000

class ConsistentTreesHDF5ArborTest4(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesHDF5Arbor
    test_filename = ["consistent_trees_hdf5/soa/forest_0.h5",
                     "consistent_trees_hdf5/soa/forest_0.h5"]
    num_data_files = 2
    tree_skip = 20000

class RockstarArborTest(TempDirTest, ArborTest):
    arbor_type = RockstarArbor
    test_filename = "rockstar/rockstar_halos/out_0.list"
    num_data_files = 65

class TreeFarmArborDescendentsTest(TempDirTest, ArborTest):
    arbor_type = TreeFarmArbor
    test_filename = "tree_farm/tree_farm_descendents/fof_subhalo_tab_000.0.h5"
    num_data_files = 51

class TreeFarmArborAncestorsTest(TempDirTest, ArborTest):
    arbor_type = TreeFarmArbor
    test_filename = "tree_farm/tree_farm_ancestors/fof_subhalo_tab_017.0.h5"
    num_data_files = 34

class LHaloTreeArborTest(TempDirTest, ArborTest):
    arbor_type = LHaloTreeArbor
    test_filename = "lhalotree/trees_063.0"
    groups = ("forest", "tree", "prog")
    tree_skip = 100
