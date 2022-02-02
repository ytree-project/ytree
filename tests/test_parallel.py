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
    base_filename = "tiny_ctrees/locations.dat"
    test_filename = "test_arbor/test_arbor.h5"
    test_script = None
    ncores = 4

    @property
    def test_script_path(self):
        return os.path.join(os.path.dirname(__file__), self.test_script)

    def check_values(self, arbor, my_args):
        group = my_args[0]
        assert_array_equal(arbor["test_field"], 2 * arbor["mass"])
        for tree in arbor:
            assert_array_equal(tree[group, "test_field"], 2 * tree[group, "mass"])

    @unittest.skipIf(MPI is None, "mpi4py not installed")
    def test_parallel(self):

        for i, my_args in enumerate(self.arg_sets):
            with self.subTest(i=i):

                # test_data_path = self.prepare_data()
                args = [self.test_script_path, self.base_filename, self.test_filename] + \
                    [str(arg) for arg in my_args]
                comm = MPI.COMM_SELF.Spawn(sys.executable, args=args, maxprocs=self.ncores)
                comm.Disconnect()

                test_arbor = ytree.load(self.test_filename)
                self.check_values(test_arbor, my_args)

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
