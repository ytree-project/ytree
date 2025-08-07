from ytree.frontends.ahf import \
    AHFArbor, \
    AHFCRMArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class AHFArborTest(TempDirTest, ArborTest):
    arbor_type = AHFArbor
    test_filename = "ahf_halos/snap_N64L16_000.parameter"
    num_data_files = 136
    tree_skip = 100

class AHFCRMArborTest(TempDirTest, ArborTest):
    arbor_type = AHFCRMArbor
    test_filename = "AHF_100_tiny/GIZMO-NewMDCLUSTER_0047.snap_128.parameter"
    num_data_files = 5
    tree_skip = 100

class AHFNameConfigArborTest(TempDirTest, ArborTest):
    arbor_type = AHFArbor
    test_filename = "B25_N256_CDM_1LPT/AHF.B25_N256_CDM_1LPT.snap_055.parameter"
    load_kwargs = {"name_config":
                       {"ahf_prefix": "AHF.B25_N256_CDM_1LPT",
                        "mtree_prefix": "MTREE.B25_N256_CDM_1LPT.z39_adapt",
                        "mtree_suffix": ".AHF_croco"}}
    num_data_files = 2
    tree_skip = 100
