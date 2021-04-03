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
