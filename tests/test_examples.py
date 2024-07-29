"""
tests for example scripts



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from ytree.utilities.testing import \
    ExampleScriptTest, \
    TempDirTest

class TestPlotMostMassive(TempDirTest, ExampleScriptTest):
    script_filename = "plot_most_massive.py"
    input_filename = "tiny_ctrees/locations.dat"
    output_files = ("most_massive.png",)

class TestPlotMostHalos(TempDirTest, ExampleScriptTest):
    script_filename = "plot_most_halos.py"
    input_filename = "tiny_ctrees/locations.dat"
    output_files = ("most_halos.png",)

class TestHaloAge(TempDirTest, ExampleScriptTest):
    ncores = 2
    script_filename = "halo_age.py"
    input_filename = "tiny_ctrees/locations.dat"
    output_files = (
        "halo_age/halo_age-analysis.h5",
        "halo_age/halo_age.h5",
        "halo_age/halo_age_0000-analysis.h5",
        "halo_age/halo_age_0000.h5"
    )

class TestHaloSignificance(TempDirTest, ExampleScriptTest):
    ncores = 2
    script_filename = "halo_significance.py"
    input_filename = "tiny_ctrees/locations.dat"
    output_files = (
        "halo_significance/halo_significance-analysis.h5",
        "halo_significance/halo_significance.h5",
        "halo_significance/halo_significance_0000-analysis.h5",
        "halo_significance/halo_significance_0000.h5"
    )
