import os
import sys

from ytree.testing.utilities import run_command
from ytree.utilities.io import dirname
from ytree.utilities.loading import check_path

try:
    from mpi4py import MPI
except ModuleNotFoundError:
    MPI = None


class ExampleScriptTest:
    """
    Tests for the code examples.
    """

    script_filename = None
    input_filename = None
    timeout = 60
    output_files = ()
    ncores = 1

    def test_example(self):
        if self.script_filename is None:
            return

        if self.input_filename is not None:
            try:
                check_path(self.input_filename)
            except IOError:
                self.skipTest("test file missing")

        source_dir = dirname(__file__, level=3)
        script_path = os.path.join(
            source_dir, "doc", "source", "examples", self.script_filename
        )

        if self.ncores > 1:
            if MPI is None:
                self.skipTest("mpi4py not installed")
            comm = MPI.COMM_SELF.Spawn(
                sys.executable, args=[script_path], maxprocs=self.ncores
            )
            comm.Barrier()
            comm.Disconnect()
        else:
            command = f"{sys.executable} {script_path}"
            assert run_command(command, timeout=self.timeout)

        for fn in self.output_files:
            assert os.path.exists(fn)
