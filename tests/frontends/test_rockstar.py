from ytree.frontends.rockstar import \
    RockstarArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class RockstarArborTest(TempDirTest, ArborTest):
    arbor_type = RockstarArbor
    test_filename = "rockstar/rockstar_halos/out_0.list"
    num_data_files = 65
    tree_skip = 10
