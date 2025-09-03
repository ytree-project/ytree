import numpy as np
import pytest
import sys

from numpy.testing import assert_array_equal
from unittest import skipIf

from ytree.data_structures.load import load

try:
    from mpi4py import MPI
except ModuleNotFoundError:
    MPI = None


class ParallelTest:
    """
    Test class for ytree parallelism.
    """

    base_filename = "tiny_ctrees/locations.dat"
    test_filename = "test_arbor/test_arbor.h5"
    test_script = None
    ncores = 4

    def check_values(self, arbor):
        group = self.args[1]

        if "nodes" in group:
            increment = int(group.split("-")[1])
        else:
            increment = None

        assert_array_equal(arbor["test_field"], 2 * arbor["mass"])
        for tree in arbor:
            if increment is None:
                assert_array_equal(tree[group, "test_field"], 2 * tree[group, "mass"])

            else:
                all_inds = np.arange(tree.tree_size)
                my_inds = all_inds[::increment]
                select = np.isin(all_inds, my_inds)
                assert_array_equal(
                    tree["forest", "test_field"][select],
                    2 * tree["forest", "mass"][select],
                )

                # the ones we didn't do should all be -1
                assert_array_equal(
                    tree["forest", "test_field"][~select],
                    -np.ones_like(tree["forest", "test_field"][~select]),
                )

    @skipIf(MPI is None, "mpi4py not installed")
    @pytest.mark.parallel
    def test_parallel(self):
        args = [self.test_script, self.base_filename, self.test_filename] + [
            str(arg) for arg in self.args
        ]
        comm = MPI.COMM_SELF.Spawn(sys.executable, args=args, maxprocs=self.ncores)
        comm.Barrier()
        comm.Disconnect()

        test_arbor = load(self.test_filename)
        self.check_values(test_arbor)
