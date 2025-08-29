from ytree.frontends.consistent_trees import ConsistentTreesGroupArbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class ConsistentTreesGroupArborTest(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesGroupArbor
    test_filename = "tiny_ctrees/locations.dat"
    num_data_files = 8
    custom_vector_fields = (
        ("a_ratio", ("b_to_a", "c_to_a")),
        ("bunch_of_rs", ("r200c", "r200b", "r500c", "r500b")),
    )

    def test_data_files(self):
        self.arbor._plant_trees()
        ArborTest.test_data_files(self)
