from ytree.frontends.ahf import AHFCRMArbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class AHFCRMArborTest(TempDirTest, ArborTest):
    arbor_type = AHFCRMArbor
    test_filename = "AHF_100_tiny/GIZMO-NewMDCLUSTER_0047.snap_128.parameter"
    num_data_files = 5
    tree_skip = 100
    slow = True
