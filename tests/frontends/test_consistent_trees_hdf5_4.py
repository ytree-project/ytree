from ytree.frontends.consistent_trees_hdf5 import ConsistentTreesHDF5Arbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class ConsistentTreesHDF5ArborTest4(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesHDF5Arbor
    test_filename = [
        "consistent_trees_hdf5/soa/forest_0.h5",
        "consistent_trees_hdf5/soa/forest_0.h5",
    ]
    num_data_files = 2
    tree_skip = 20000
