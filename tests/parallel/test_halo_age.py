"""
tests for example halo age script



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


class TestHaloAge(TempDirTest, ExampleScriptTest):
    ncores = 2
    script_filename = "halo_age.py"
    input_filename = "tiny_ctrees/locations.dat"
    output_files = (
        "halo_age/halo_age-analysis.h5",
        "halo_age/halo_age.h5",
        "halo_age/halo_age_0000-analysis.h5",
        "halo_age/halo_age_0000.h5",
    )
