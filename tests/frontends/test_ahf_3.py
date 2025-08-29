from ytree.frontends.ahf import AHFArbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class AHFNameConfigArborTest(TempDirTest, ArborTest):
    arbor_type = AHFArbor
    test_filename = "B25_N256_CDM_1LPT/AHF.B25_N256_CDM_1LPT.snap_055.parameter"
    load_kwargs = {
        "name_config": {
            "ahf_prefix": "AHF.B25_N256_CDM_1LPT",
            "mtree_prefix": "MTREE.B25_N256_CDM_1LPT.z39_adapt",
            "mtree_suffix": ".AHF_croco",
        }
    }
    num_data_files = 2
    tree_skip = 100
