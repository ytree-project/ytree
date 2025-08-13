from ytree.frontends.consistent_trees import \
    ConsistentTreesGroupArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class ConsistentTreesGroupArborTest(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesGroupArbor
    test_filename = "tiny_ctrees/locations.dat"
    num_data_files = 8

    def test_data_files(self):
        self.arbor._plant_trees()
        ArborTest.test_data_files(self)
