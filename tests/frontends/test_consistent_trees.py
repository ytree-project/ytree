from ytree.frontends.consistent_trees import \
    ConsistentTreesGroupArbor, \
    ConsistentTreesArbor, \
    ConsistentTreesHlistArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

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
