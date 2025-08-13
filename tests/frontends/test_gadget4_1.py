from ytree.frontends.gadget4 import \
    Gadget4Arbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class Gadget4ArborSingleTest(TempDirTest, ArborTest):
    arbor_type = Gadget4Arbor
    test_filename = "gadget4/trees/trees.hdf5"
    groups = ("forest", "tree", "prog")
    num_data_files = 1
    tree_skip = 100
