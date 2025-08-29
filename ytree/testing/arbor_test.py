import numpy as np
from numpy.testing import assert_equal, assert_array_equal

from ytree.data_structures.load import load
from ytree.frontends.ytree import YTreeArbor
from ytree.testing.utilities import (
    compare_arbors,
    get_random_trees,
    verify_get_leaf_nodes,
    verify_get_node,
    verify_get_root_nodes,
)
from ytree.utilities.loading import get_path
from ytree.utilities.logger import ytreeLogger as mylog


class ArborTest:
    """
    A battery of tests for all frontends.
    """

    arbor_type = None
    test_filename = None
    load_kwargs = None
    load_callback = None
    groups = ("tree", "prog")
    num_data_files = None
    tree_skip = 1
    custom_vector_fields = None
    slow = False

    _arbor = None

    @property
    def arbor(self):
        if self._arbor is None:
            try:
                self.test_filename = get_path(self.test_filename)
            except IOError:
                self.skipTest("test file missing")

            if self.load_kwargs is None:
                self.load_kwargs = {}

            self._arbor = load(self.test_filename, **self.load_kwargs)
            if self.load_callback is not None:
                self.load_callback(self._arbor)
        return self._arbor

    def test_arbor_type(self):
        assert isinstance(self.arbor, self.arbor_type)

    def test_data_files(self):
        if self.num_data_files is None:
            return
        assert_equal(
            len(self.arbor.data_files),
            self.num_data_files,
            err_msg=f"Incorrect number of data files for {self.arbor}.",
        )

    def test_get_root_nodes(self):
        for my_tree in get_random_trees(self.arbor, 47457, 5):
            verify_get_root_nodes(my_tree)

    def test_get_roor_nodes_nonroot(self):
        my_tree = list(self.arbor[0].ancestors)[0]
        verify_get_root_nodes(my_tree)

    def test_get_leaf_nodes(self):
        for my_tree in get_random_trees(self.arbor, 41153, 5):
            verify_get_leaf_nodes(my_tree)

    def test_get_leaf_nodes_ungrown_nonroot(self):
        my_tree = list(self.arbor[0].ancestors)[0]
        verify_get_leaf_nodes(my_tree)

    def test_get_node(self):
        for my_tree in get_random_trees(self.arbor, 47988, 5):
            verify_get_node(my_tree)

            ihalos = np.arange(1, my_tree.tree_size)
            gen = np.random.default_rng(312)
            gen.shuffle(ihalos)
            for ihalo in ihalos[:3]:
                my_halo = my_tree.get_node("forest", ihalo)
                verify_get_node(my_halo)

    def test_get_node_ungrown_nonroot(self):
        my_tree = list(self.arbor[0].ancestors)[0]
        my_halo = my_tree.get_node("forest", 0)
        node_list = list(my_tree["forest"])
        assert_equal(my_halo.uid, node_list[0].uid)

    def test_reset_node(self):
        t = self.arbor[0]
        ts0 = len(list(t["tree"]))
        f0 = dict((field, t["tree", field]) for field in ["uid", "desc_uid"])

        assert self.arbor.is_setup(t)
        assert self.arbor.is_grown(t)

        self.arbor.reset_node(t)

        for attr in self.arbor._reset_attrs:
            assert getattr(t, attr) is None
        assert_equal(len(t.field_data), 0)
        assert not self.arbor.is_setup(t)
        assert not self.arbor.is_grown(t)

        assert_equal(
            len(list(t["tree"])),
            ts0,
            err_msg=f"Trees are not the same size after resetting for {self.arbor}.",
        )

        for field in f0:
            assert_array_equal(
                t["tree", field],
                f0[field],
                err_msg=f"Tree field {field} not the same after resetting for {self.arbor}.",
            )

    def test_reset_nonroot(self):
        t = self.arbor[0]
        node = list(t["tree"])[1]
        ts0 = len(list(node["tree"]))
        f0 = dict((field, node["tree", field]) for field in ["uid", "desc_uid"])

        self.arbor.reset_node(node)

        assert_equal(
            len(list(node["tree"])),
            ts0,
            err_msg=f"Trees are not the same size after resetting for {self.arbor}.",
        )

        for field in f0:
            assert_array_equal(
                node["tree", field],
                f0[field],
                err_msg=f"Tree field {field} not the same after resetting for {self.arbor}.",
            )

    def test_save_and_reload(self):
        skip = self.tree_skip
        if skip > 1:
            trees = list(self.arbor[::skip])
        else:
            trees = None

        fn = self.arbor.save_arbor(trees=trees)

        save_arbor = load(fn)
        if self.load_callback is not None:
            self.load_callback(save_arbor)

        assert isinstance(save_arbor, YTreeArbor)
        compare_arbors(save_arbor, self.arbor, groups=self.groups, skip2=skip)

    def test_vector_fields(self):
        a = self.arbor
        t = a[0]

        if self.custom_vector_fields is not None:
            for vfield, cfields in self.custom_vector_fields:
                a.add_vector_field(vfield, vector_components=cfields)

        for field in a.field_info.vector_fields:
            mylog.info(f"Comparing vector field: {field}.")
            magfield = np.sqrt((a[field] ** 2).sum(axis=1))
            assert_array_equal(
                a[f"{field}_magnitude"],
                magfield,
                err_msg=f"Magnitude field incorrect: {field}.",
            )

            cfields = a.field_info[field]["vector_components"]

            for i, cfield in enumerate(cfields):
                assert_array_equal(
                    a[cfield],
                    a[field][:, i],
                    err_msg=(
                        f"Arbor vector field {field} does not match in dimension {i}."
                    ),
                )

                assert_array_equal(
                    t[cfield],
                    t[field][i],
                    err_msg=(
                        f"Tree vector field {field} does not match in dimension {i}."
                    ),
                )

                for group in ["prog", "tree"]:
                    assert_array_equal(
                        t[group, cfield],
                        t[group, field][:, i],
                        err_msg=(
                            f"{group} vector field {field} does not match "
                            f"in dimension {i}."
                        ),
                    )
