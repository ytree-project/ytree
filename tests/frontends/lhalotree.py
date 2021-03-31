from ytree.frontends.lhalotree import \
    LHaloTreeArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class LHaloTreeArborTest(TempDirTest, ArborTest):
    arbor_type = LHaloTreeArbor
    test_filename = "lhalotree/trees_063.0"
    groups = ("forest", "tree", "prog")
    tree_skip = 100
