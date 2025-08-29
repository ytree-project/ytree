"""
tests for saving arbors and trees



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from ytree.testing.utilities import compare_trees, requires_file, TempDirTest

import ytree

CT = "consistent_trees/tree_0_0_0.dat"
TCT = "tiny_ctrees/locations.dat"


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
        assert sorted(["mass", "redshift", "uid", "desc_uid"]) == sorted(a2.field_list)

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

    @requires_file(TCT)
    def test_save_in_place_true(self):
        a = ytree.load(TCT)

        fn = a.save_arbor()
        a2 = ytree.load(fn)
        a2.add_analysis_field("test_field", "", default=-1.0)

        # this should be only a subset of all trees
        trees = list(a2[a2["mass"] > 3e11])
        for tree in trees:
            for node in tree["forest"]:
                node["test_field"] = 5

        fn2 = a2.save_arbor(trees=trees)
        a3 = ytree.load(fn2)

        # check if the arbor size is unchanged
        assert a3.size == a.size
        # check if number of trees with altered field is right
        assert (a3["test_field"] == 5).sum() == len(trees)

        trees = a3[a3["mass"] > 3e11]
        for tree in trees:
            assert (tree["forest", "test_field"] == 5).all()

    @requires_file(TCT)
    def test_save_in_place_false(self):
        a = ytree.load(TCT)

        fn = a.save_arbor()
        a2 = ytree.load(fn)
        a2.add_analysis_field("test_field", "", default=-1.0)

        # this should be only a subset of all trees
        trees = list(a2[a2["mass"] > 3e11])
        for tree in trees:
            for node in tree["forest"]:
                node["test_field"] = 5

        fn2 = a2.save_arbor(trees=trees, save_in_place=False)
        a3 = ytree.load(fn2)

        # check if the arbor size changed (it should be!)
        assert a3.size == len(trees)
        # check if number of trees with altered field is right
        assert (a3["test_field"] == 5).sum() == len(trees)

        trees = a3[:]
        for tree in trees:
            assert (tree["forest", "test_field"] == 5).all()

    @requires_file(TCT)
    def test_save_roots_only(self):
        a = ytree.load(TCT)

        fn = a.save_arbor()
        a2 = ytree.load(fn)
        a2.add_analysis_field("test_field", "", default=-1.0)

        # this should be only a subset of all trees
        trees = list(a2[a2["mass"] > 3e11])
        for tree in trees:
            for node in tree["forest"]:
                node["test_field"] = 5

        fn2 = a2.save_arbor(trees=trees, save_roots_only=True)
        a3 = ytree.load(fn2)

        # check if the arbor size is unchanged
        assert a3.size == a.size
        # check if number of trees with altered field is right
        assert (a3["test_field"] == 5).sum() == len(trees)

        trees = a3[a3["mass"] > 3e11]
        for tree in trees:
            # the root should be changed, but the rest of the tree should not
            assert tree["test_field"] == 5
            assert (tree["forest", "test_field"][1:] == -1).all()

    @requires_file(TCT)
    def test_save_in_place_roots_only(self):
        a = ytree.load(TCT)

        fn = a.save_arbor()
        a2 = ytree.load(fn)
        a2.add_analysis_field("test_field", "", default=-1.0)

        trees = list(a2[a2["mass"] > 3e11])
        with self.assertRaises(ValueError):
            a2.save_arbor(trees=trees, save_in_place=False, save_roots_only=True)
