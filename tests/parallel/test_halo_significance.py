"""
tests for example halo significance script



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


class TestHaloSignificance(TempDirTest, ExampleScriptTest):
    ncores = 2
    script_filename = "halo_significance.py"
    input_filename = "tiny_ctrees/locations.dat"
    output_files = (
        "halo_significance/halo_significance-analysis.h5",
        "halo_significance/halo_significance.h5",
        "halo_significance/halo_significance_0000-analysis.h5",
        "halo_significance/halo_significance_0000.h5",
    )
