"""
tests for parallel iterators



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from numpy.testing import assert_array_equal
import os
import sys
import unittest
import ytree

from ytree.utilities.testing import TempDirTest

try:
    from mpi4py import MPI
except ModuleNotFoundError:
    MPI = None

class ParallelTest:
    test_filename = "tiny_ctrees/locations.dat"
    test_script = None
    ncores = None

    @unittest.skipIf(MPI is None, "mpi4py not installed")
    def test_parallel(self):

        for i, my_args in enumerate(self.arg_sets):
            with self.subTest(i=i):

                a = ytree.load(self.test_filename)
                fn = a.save_arbor(trees=a[:8])

                filename = os.path.join(os.path.dirname(__file__), self.test_script)

                group = my_args[0]
                args = [filename, fn] + [str(arg) for arg in my_args]
                comm = MPI.COMM_SELF.Spawn(sys.executable, args=args, maxprocs=4)
                comm.Disconnect()

                a2 = ytree.load(fn)
                assert_array_equal(a2["test_field"], 2 * a2["mass"])
                for tree in a2:
                    assert_array_equal(tree[group, "test_field"], 2 * tree[group, "mass"])

class ParallelTreesTest(TempDirTest, ParallelTest):
    test_script = "parallel/parallel_trees.py"
    arg_sets = (
        ("forest", 0, 0, 4),
        ("tree",   0, 0, 4),
        ("prog",   0, 0, 4),
        ("forest", 0, 0,  ), # sets save_every to None
        ("forest", 2, 0, 4),
        ("forest", 0, 1, 4),
    )

class ParallelTreeNodesTest(TempDirTest, ParallelTest):
    test_script = "parallel/parallel_tree_nodes.py"
    arg_sets = (
        ("forest", 0, 0),
        ("tree",   0, 0),
        ("prog",   0, 0),
        ("forest", 2, 0),
        ("forest", 0, 1),
    )

class ParallelNodesTest(TempDirTest, ParallelTest):
    test_script = "parallel/parallel_nodes.py"
    arg_sets = (
        ("forest", 1, 0, 0, 0, 4),
        ("tree",   1, 0, 0, 0, 4),
        ("prog",   1, 0, 0, 0, 4),
        ("forest", 0, 1, 0, 0, 4),
        ("forest", 1, 0, 0, 0,  ), # sets save_every to None
        ("forest", 1, 0, 0, 1, 4),
        ("forest", 0, 1, 1, 0, 4),
    )
