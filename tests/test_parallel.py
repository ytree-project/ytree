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

        for i, (my_args, my_cores) in enumerate(zip(self.arg_sets, self.core_sets)):
            with self.subTest(i=i):

                a = ytree.load(self.test_filename)
                fn = a.save_arbor()

                filename = os.path.join(os.path.dirname(__file__), self.test_script)

                args = [filename, fn] + [str(arg) for arg in my_args]
                comm = MPI.COMM_SELF.Spawn(sys.executable, args=args, maxprocs=my_cores)
                comm.Disconnect()

                a2 = ytree.load(fn)
                assert_array_equal(a2["test_field"], 2 * a2["mass"])
                for tree in a2:
                    assert_array_equal(tree["forest", "test_field"], 2 * tree["forest", "mass"])

class ParallelTreesTest(TempDirTest, ParallelTest):
    test_script = "parallel/parallel_trees.py"
    core_sets = (4, 4, 4, 4)
    arg_sets = (
        (0, 0, 8),
        (0, 0), # sets save_every to None
        (2, 0, 8),
        (0, 1, 8),
    )
