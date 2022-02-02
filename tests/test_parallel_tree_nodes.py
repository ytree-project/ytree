"""
tests for parallel_tree_nodes iterator



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

class ParallelTreeNodesTest(TempDirTest, ParallelTest):
    test_script = os.path.join(script_path, "parallel/parallel_tree_nodes.py")
    arg_sets = (
        ("all", "forest", 0, 0),
        ("all", "tree",   0, 0),
        ("all", "prog",   0, 0),
        ("all", "forest", 2, 0),
        ("all", "forest", 0, 1),
    )
