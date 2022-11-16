from ytree.frontends.ahf import \
    AHFArbor, \
    AHFNewArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class AHFArborTest(TempDirTest, ArborTest):
    arbor_type = AHFArbor
    test_filename = "ahf_halos/snap_N64L16_000.parameter"
    num_data_files = 136
    tree_skip = 100

class AHFNewArborTest(TempDirTest, ArborTest):
    arbor_type = AHFNewArbor
    test_filename = "AHF_100_tiny/GIZMO-NewMDCLUSTER_0047.snap_128.parameter"
    num_data_files = 5
    tree_skip = 100
