from ytree.arbor.frontends.consistent_trees import \
    ConsistentTreesArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class ConsistentTreesArborTest(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesArbor
    test_filename = "rockstar_halos/trees/tree_0_0_0.dat"
