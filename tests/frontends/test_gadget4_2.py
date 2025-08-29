from ytree.frontends.gadget4 import Gadget4Arbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class Gadget4ArborMultipleTest(TempDirTest, ArborTest):
    arbor_type = Gadget4Arbor
    test_filename = "gadget4/treedata/trees.0.hdf5"
    groups = ("forest", "tree", "prog")
    num_data_files = 64
    tree_skip = 100
