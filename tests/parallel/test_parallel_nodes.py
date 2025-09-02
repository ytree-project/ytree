"""
tests for parallel_nodes iterator



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
test_script = os.path.join(script_path, "parallel_nodes.py")


class ParallelNodesTest1(TempDirTest, ParallelTest):
    test_script = test_script
    args = ("all", "forest", 1, 0, 0, 0, 4)


class ParallelNodesTest2(TempDirTest, ParallelTest):
    test_script = test_script
    args = ("all", "tree", 1, 0, 0, 0, 4)


class ParallelNodesTest3(TempDirTest, ParallelTest):
    test_script = test_script
    args = ("all", "prog", 1, 0, 0, 0, 4)


class ParallelNodesTest4(TempDirTest, ParallelTest):
    test_script = test_script
    args = ("all", "forest", 0, 1, 0, 0, 4)


class ParallelNodesTest5(TempDirTest, ParallelTest):
    test_script = test_script
    # sets save_every to None
    args = ("all", "forest", 1, 0, 0, 0)


class ParallelNodesTest6(TempDirTest, ParallelTest):
    test_script = test_script
    args = ("all", "forest", 1, 0, 0, 1, 4)


class ParallelNodesTest7(TempDirTest, ParallelTest):
    test_script = test_script
    args = ("all", "forest", 0, 1, 1, 0, 4)


class ParallelNodesTest8(TempDirTest, ParallelTest):
    ncores = 2
    test_script = test_script
    # sets save_every to None
    args = ("nonroot", "tree", 1, 0, 0, 0)


class ParallelNodesTest9(TempDirTest, ParallelTest):
    ncores = 2
    test_script = test_script
    # sets save_every to None
    args = ("nonroot", "tree", 0, 1, 0, 0)
