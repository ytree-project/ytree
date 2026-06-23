"""
tests for example accretion rates script



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from ytree.testing.example_script_test import ExampleScriptTest
from ytree.testing.utilities import TempDirTest


class TestMergerAccretionRates(TempDirTest, ExampleScriptTest):
    ncores = 2
    script_filename = "merger_accretion_rates.py"
    input_filename = "tiny_ctrees/locations.dat"
    output_files = (
        "accretion_rates/accretion_rates-analysis.h5",
        "accretion_rates/accretion_rates.h5",
        "accretion_rates/accretion_rates_0000-analysis.h5",
        "accretion_rates/accretion_rates_0000.h5",
    )
