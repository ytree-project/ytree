# import numpy as np
import os
from yt.testing import \
    requires_file
from ytree.arbor.frontends.rockstar import \
    RockstarArbor
from ytree.arbor.frontends.rockstar.misc import \
    f_text_block
from ytree.arbor.frontends.ytree import \
    YTreeArbor
from ytree.utilities.testing import \
    compare_arbors, \
    test_data_dir, \
    TempDirTest

import ytree

R0 = os.path.join(test_data_dir,
                  "rockstar_halos/out_0.list")
R63 = os.path.join(test_data_dir,
                   "rockstar_halos/out_63.list")

class RockstarArborTest(TempDirTest):
    @requires_file(R0)
    def test_rs_arbor(self):
        a1 = ytree.load(R0)
        assert isinstance(a1, RockstarArbor)
        m1 = a1["mass"]

        fn = a1.save_arbor("arbor_rs")
        a2 = ytree.load(fn)
        assert isinstance(a2, YTreeArbor)
        m2 = a2["mass"]

        assert (m1 == m2).all()
        for gtype in ["tree", "prog"]:
            compare_arbors(a2, a1, group=gtype)

        # i1 = np.argsort(m1.d)[::-1][0]
        # fn = a1[i1].save_tree()
        # a3 = load(fn)
        # assert isinstance(a3, ArborArbor)
        # for field in a1.field_list:
        #     assert (a1[i1]["tree", field] == a3[0]["tree", field]).all()

        # # test saving trees from non-root positions
        # fn = a1[i1]["tree", 1].save_tree()
        # a4 = load(fn)
        # assert (a4[0]["tree", "tree_id"] == a4[0]["tree_id"]).all()
        # assert (a1[i1]["tree", 1]["tree", "desc_id"][1:] == a4[0]["tree", "desc_id"][1:]).all()
        # for field in a1.field_list:
        #     if field in ["tree_id", "desc_id"]: continue
        #     assert (a1[i1]["tree", 1]["tree", field] == a4[0]["tree", field]).all()

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
