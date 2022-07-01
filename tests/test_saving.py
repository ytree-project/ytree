"""
tests for saving arbors and trees



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from ytree.utilities.testing import \
    compare_trees, \
    requires_file, \
    TempDirTest

import ytree

CT = "consistent_trees/tree_0_0_0.dat"

class SaveArborTest(TempDirTest):
    @requires_file(CT)
    def test_default_save(self):
        a = ytree.load(CT)
        fn = a.save_arbor(max_file_size=512)

        a2 = ytree.load(fn)
        assert a.size == a2.size

    @requires_file(CT)
    def test_save_non_roots(self):
        a = ytree.load(CT)

        my_trees = [list(a[0]["tree"])[1], list(a[1]["tree"])[1]]
        fn = a.save_arbor(trees=my_trees)
        a2 = ytree.load(fn)

        fields = a2.field_list[:]
        fields.remove("desc_uid")

        for t1, t2 in zip(a2, my_trees):
            compare_trees(t1, t2, fields=fields)

    @requires_file(CT)
    def test_save_field_list(self):
        a = ytree.load(CT)

        my_trees = [list(a[0]["tree"])[1], list(a[1]["tree"])[1]]
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

        t = a[0]
        fn = t.save_tree()
        a2 = ytree.load(fn)

        fields = a2.field_list[:]
        fields.remove("desc_uid")
        compare_trees(t, a2[0], fields=fields)

    @requires_file(CT)
    def test_save_tree_nonroot(self):
        a = ytree.load(CT)

        t = list(a[0]["tree"])[1]
        fn = t.save_tree()
        a2 = ytree.load(fn)

        fields = a2.field_list[:]
        fields.remove("desc_uid")
        compare_trees(t, a2[0], fields=fields)
