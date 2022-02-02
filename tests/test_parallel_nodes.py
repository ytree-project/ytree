"""
tests for parallel_nodes iterator



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os

from ytree.utilities.testing import ParallelTest, TempDirTest

script_path = os.path.dirname(__file__)

class ParallelNodesTest(TempDirTest, ParallelTest):
    test_script = os.path.join(script_path, "parallel/parallel_nodes.py")
    arg_sets = (
        ("all", "forest", 1, 0, 0, 0, 4),
        ("all", "tree",   1, 0, 0, 0, 4),
        ("all", "prog",   1, 0, 0, 0, 4),
        ("all", "forest", 0, 1, 0, 0, 4),
        ("all", "forest", 1, 0, 0, 0,  ), # sets save_every to None
        ("all", "forest", 1, 0, 0, 1, 4),
        ("all", "forest", 0, 1, 1, 0, 4),
    )

class NonRootParallelNodesTest(ParallelNodesTest):
    ncores = 2
    arg_sets = (
        ("nonroot", "tree", 1, 0, 0, 0,  ), # sets save_every to None
        ("nonroot", "tree", 0, 1, 0, 0,  ), # sets save_every to None
    )
