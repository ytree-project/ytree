"""
tests for parallel_trees iterator



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import os

from ytree.testing.parallel_test import ParallelTest
from ytree.testing.utilities import TempDirTest

script_path = os.path.dirname(__file__)
test_script = os.path.join(script_path, "run_parallel_trees.py")


class ParallelTreesTest4(TempDirTest, ParallelTest):
    test_script = test_script
    # sets save_every to None
    args = ("all", "forest", 0, 0)
