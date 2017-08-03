"""
tests for saving arbors and trees



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os

from ytree.utilities.testing import \
    compare_trees, \
    requires_file, \
    test_data_dir, \
    TempDirTest

import ytree

CT = os.path.join(test_data_dir,
                  "consistent_trees/tree_0_0_0.dat")

class SaveArborTest(TempDirTest):
    @requires_file(CT)
    def test_save_non_roots(self):
        a = ytree.load(CT)

        my_trees = [a[0]["tree"][1], a[1]["tree"][1]]
        fn = a.save_arbor(trees=my_trees)
        a2 = ytree.load(fn)

        fields = a2.field_list[:]
        fields.remove("desc_uid")

        for t1, t2 in zip(a2, my_trees):
            compare_trees(t1, t2, fields=fields)

    @requires_file(CT)
    def test_save_field_list(self):
        a = ytree.load(CT)

        my_trees = [a[0]["tree"][1], a[1]["tree"][1]]
        fn = a.save_arbor(trees=my_trees, fields=["mass", "redshift"])
        a2 = ytree.load(fn)

        assert len(a2.field_list) == 4
        assert sorted(["mass", "redshift", "uid", "desc_uid"]) == \
          sorted(a2.field_list)

        fields = a2.field_list[:]
        fields.remove("desc_uid")

        for t1, t2 in zip(a2, my_trees):
            compare_trees(t1, t2, fields=fields)

    @requires_file(CT)
    def test_save_tree(self):
        a = ytree.load(CT)

        for t in [a[0], a[0]["tree"][1]]:
            fn = t.save_tree()
            a2 = ytree.load(fn)
        
            fields = a2.field_list[:]
            fields.remove("desc_uid")
            compare_trees(t, a2[0], fields=fields)
