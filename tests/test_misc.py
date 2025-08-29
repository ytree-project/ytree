"""
miscellaneous utility tests



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import os
from ytree.data_structures.load import load as ytree_load
from ytree.utilities.io import f_text_block
from ytree.utilities.loading import test_data_dir
from ytree.testing.utilities import requires_file, TempDirTest

R0 = os.path.join(test_data_dir, "rockstar/rockstar_halos/out_0.list")
R63 = os.path.join(test_data_dir, "rockstar/rockstar_halos/out_63.list")


@requires_file(R63)
def test_f_text_block():
    for block_size in [40, 32768]:
        lines = []
        locs = []
        f = open(R63, "r")
        for line, loc in f_text_block(f, block_size=block_size):
            lines.append(line)
            locs.append(loc)

        lines2 = []
        for loc in locs:
            f.seek(loc)
            line = f.readline()
            lines2.append(line.strip())

        for l1, l2 in zip(lines, lines2):
            assert l1 == l2


class MiscTest(TempDirTest):
    """
    Some miscellaneous tests in temporary directories
    """

    @requires_file(R0)
    def test_tree_field_clobber(self):
        """
        Test for an issue where the uid and desc_uid fields would be
        deleted if the tree was setup in the middle of getting fields.
        Fixed in PR #19: https://github.com/ytree-project/ytree/pull/19
        """
        a = ytree_load(R0)
        t = a[a["mass"].argmax()]
        t["prog", "redshift"]
        t.save_tree()


@requires_file(R0)
def test_field_access_without_tree_setup():
    """
    Test field access on non-root nodes of catalog arbors where
    setup_tree has not been called.
    Fixed in PR #20: https://github.com/ytree-project/ytree/pull/20
    """
    a = ytree_load(R0)
    t = a[a["mass"].argmax()]
    list(t.ancestors)[0]["desc_uid"]
