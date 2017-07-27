# import numpy as np
import os
from ytree.arbor.frontends.consistent_trees import \
    ConsistentTreesArbor
from ytree.arbor.frontends.ytree import \
    YTreeArbor
from ytree.utilities.testing import \
    compare_arbors, \
    requires_file, \
    test_data_dir, \
    TempDirTest

import ytree

CT = os.path.join(test_data_dir,
                  "rockstar_halos/trees/tree_0_0_0.dat")

class ConsistentTreesArborTest(TempDirTest):
    @requires_file(CT)
    def test_ct_arbor(self):
        a1 = ytree.load(CT)
        assert isinstance(a1, ConsistentTreesArbor)
        m1 = a1["mass"]

        fn = a1.save_arbor("arbor_ct")
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
