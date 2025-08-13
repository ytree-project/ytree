from ytree.frontends.consistent_trees_hdf5 import \
    ConsistentTreesHDF5Arbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class ConsistentTreesHDF5ArborTest1(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesHDF5Arbor
    test_filename = "consistent_trees_hdf5/soa/forest.h5"
    num_data_files = 1
    tree_skip = 10000
