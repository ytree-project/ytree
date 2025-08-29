from ytree.frontends.consistent_trees_hdf5 import ConsistentTreesHDF5Arbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class ConsistentTreesHDF5ArborTest3(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesHDF5Arbor
    test_filename = "consistent_trees_hdf5/soa/forest_0.h5"
    num_data_files = 1
    tree_skip = 10000
