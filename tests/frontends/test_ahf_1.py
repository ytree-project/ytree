from ytree.frontends.ahf import \
    AHFArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class AHFArborTest(TempDirTest, ArborTest):
    arbor_type = AHFArbor
    test_filename = "ahf_halos/snap_N64L16_000.parameter"
    num_data_files = 136
    tree_skip = 100
