"""
test for documented examples



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from ytree.utilities.testing import \
    requires_file, \
    ExampleScriptTest, \
    TempDirTest

import ytree

CTG = "tiny_ctrees/locations.dat"

def calc_a50(node):
    # main progenitor masses
    pmass = node["prog", "mass"]

    mh = 0.5 * node["mass"]
    m50 = pmass <= mh

    if not m50.any():
        th = node["scale_factor"]
    else:
        pscale = node["prog", "scale_factor"]
        # linearly interpolate
        i = np.where(m50)[0][0]
        slope = (pscale[i-1] - pscale[i]) / (pmass[i-1] - pmass[i])
        th = slope * (mh - pmass[i]) + pscale[i]

    node["a50"] = th

def calc_significance(node):
   if node.descendent is None:
       dt = 0. * node["time"]
   else:
       dt = node.descendent["time"] - node["time"]

   sig = node["mass"] * dt
   if node.ancestors is not None:
       for anc in node.ancestors:
           sig += calc_significance(anc)

   node["significance"] = sig
   return sig

class ExampleTest(TempDirTest):
    """
    Tests of the examples in the documentation
    """

    @requires_file(CTG)
    def test_halo_age(self):
        """
        Test halo age example.
        """

        a = ytree.load(CTG)
        a.add_analysis_field("a50", "")

        ap = ytree.AnalysisPipeline()
        ap.add_operation(calc_a50)

        trees = list(a[:])
        for tree in trees:
            ap.process_target(tree)

        fn = a.save_arbor(filename="halo_age", trees=trees)
        a2 = ytree.load(fn)
        print (a2[0]["a50"])

    @requires_file(CTG)
    def test_significance(self):
        """
        Test John Wise's significance.
        """

        a = ytree.load(CTG)
        a.add_analysis_field("significance", "Msun*Myr")

        ap = ytree.AnalysisPipeline()
        ap.add_operation(calc_significance)

        trees = list(a[:])
        for tree in trees:
            ap.process_target(tree)

        fn = a.save_arbor(filename="significance", trees=trees)
        a2 = ytree.load(fn)
        a2.set_selector("max_field_value", "significance")
        prog = list(a2[0]["prog"])
        print (prog)

class TestPlotMostMassive(TempDirTest, ExampleScriptTest):
    script_filename = "plot_most_massive.py"
    timeout = 60
    output_files = ("most_massive.png",)

class TestPlotMostHalos(TempDirTest, ExampleScriptTest):
    script_filename = "plot_most_halos.py"
    timeout = 60
    output_files = ("most_halos.png",)
