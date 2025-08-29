"""
tests for analysis pipeline



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import numpy as np
from numpy.testing import assert_array_equal, assert_equal
import os
import ytree

from ytree.testing.utilities import requires_file, TempDirTest

TCL = "tiny_ctrees/locations.dat"


def set_test_field(node, output_dir=None):
    node["test_field"] = 2 * node["mass"]


def minimum_mass_filter(node, value):
    return node["mass"] > value


def set_always(node):
    node["test_always"] = 1


def my_recipe(ap):
    ap.add_operation(minimum_mass_filter, 3e11)
    ap.add_operation(set_test_field, output_dir="my_analysis")
    ap.add_operation(set_always, always_do=True)


class AnalysisPipelineTest(TempDirTest):
    test_filename = TCL

    def test_pipeline(self):
        a = ytree.load(self.test_filename)
        fn = a.save_arbor(trees=a[:8])

        a = ytree.load(fn)
        if "test_field" not in a.field_list:
            a.add_analysis_field("test_field", default=-1, units="Msun")
            a.add_analysis_field("test_always", dtype=int, default=0, units="")

        ap = ytree.AnalysisPipeline(output_dir="analysis")
        ap.add_recipe(my_recipe)

        trees = list(a[:])
        for tree in trees:
            for node in tree["forest"]:
                ap.process_target(node)

        assert os.path.exists("analysis/my_analysis")

        fn = a.save_arbor(trees=trees)
        a2 = ytree.load(fn)

        mf = a2["mass"] > 3e11
        assert_array_equal(a2["test_field"][mf], 2 * a2["mass"][mf])
        assert_array_equal(a2["test_field"][~mf], -np.ones((~mf).sum()))
        assert_equal(a2["test_always"].sum(), a2.size)

        for tree in a2:
            mf = tree["forest", "mass"] > 3e11
            assert_array_equal(
                tree["forest", "test_field"][mf], 2 * tree["forest", "mass"][mf]
            )
            assert_array_equal(tree["forest", "test_field"][~mf], -np.ones((~mf).sum()))


def increment_counter(node):
    if getattr(node, "count", None) is None:
        node.count = 0
    node["count"] = node.count
    node.count += 1


@requires_file(TCL)
def test_handoff_attrs():
    a = ytree.load(TCL)
    a.add_analysis_field("count", dtype=int, default=0, units="")

    ap = ytree.AnalysisPipeline(output_dir=".")
    ap.add_operation(increment_counter)

    nodes = list(a[:])
    for node in nodes:
        ap.process_target(node, handoff_attrs=["count"])

    for i, node in enumerate(nodes):
        # check value was set off of persistent attribute
        assert i == node["count"]
        # check the attribute as been deleted
        assert hasattr(node, "count") is False


def do_nothing(node):
    return


global_count = 0


def increment_global_counter():
    global global_count
    global_count += 1


@requires_file(TCL)
def test_preprocess():
    a = ytree.load(TCL)

    ap = ytree.AnalysisPipeline(output_dir=".")
    ap.add_operation(do_nothing, preprocess_function=increment_global_counter)

    nodes = list(a[:])
    for node in nodes:
        ap.process_target(node)

    assert global_count == 1
