from ytree.frontends.treefarm import \
    TreeFarmArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class TreeFarmArborDescendentsTest(TempDirTest, ArborTest):
    arbor_type = TreeFarmArbor
    test_filename = "tree_farm/tree_farm_descendents/fof_subhalo_tab_000.0.h5"
    num_data_files = 51
