"""
miscellaneous utility tests



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016-2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os
from ytree.arbor.frontends.rockstar.misc import \
    f_text_block
from ytree.utilities.testing import \
    requires_file, \
    test_data_dir

R63 = os.path.join(test_data_dir, "rockstar_halos/out_63.list")

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
