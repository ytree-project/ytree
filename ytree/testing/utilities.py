"""
testing utilities



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import h5py
import numpy as np
import os
import shutil
import subprocess
import tempfile
from unittest import TestCase

from numpy.dtypes import StringDType
from numpy.testing import assert_equal, assert_almost_equal, assert_array_equal
from yt.funcs import get_pbar

from ytree.utilities.loading import get_path
from ytree.utilities.logger import ytreeLogger as mylog


def requires_file(filename):
    def ffalse(func):
        return None

    def ftrue(func):
        return func

    if not isinstance(filename, list):
        filename = [filename]
    try:
        [get_path(fn) for fn in filename]
    except IOError:
        return ffalse
    return ftrue


class TempDirTest(TestCase):
    """
    A test class that runs in a temporary directory and
    removes it afterward.
    """

    def setUp(self):
        self.curdir = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.curdir)
        shutil.rmtree(self.tmpdir)


def run_command(command, timeout=None):
    try:
        proc = subprocess.run(command, shell=True, timeout=timeout)
        if proc.returncode == 0:
            success = True
        else:
            success = False
    except subprocess.TimeoutExpired:
        print("Process reached timeout of %d s. (%s)" % (timeout, command))
        success = False
    except KeyboardInterrupt:
        print("Killed by keyboard interrupt!")
        success = False
    return success


def get_tree_split(arbor):
    """
    Get a few separate ancestors from a tree.
    """
    ancs = None
    for tree in arbor:
        for halo in tree["tree"]:
            ancs = list(halo.ancestors)
            if len(ancs) > 1:
                break

    if ancs is None:
        raise RuntimeError("Could not find nodes to test with.")
    return ancs


def get_random_trees(arbor, seed, n):
    """
    Get n random trees from the arbor.
    """

    gen = np.random.default_rng(708)
    itrees = np.arange(arbor.size)
    gen.shuffle(itrees)
    for itree in itrees[:5]:
        yield arbor[itree]


def get_stringsafe_compare_arrays(arr1, arr2):
    """
    Convert to stringy arrays to a common type for comparison.
    """

    if StringDType() in (arr1.dtype, arr2.dtype):
        # Python 3.9 and earlier require this. Otherwise, you end up
        # with  "b'Alexander'" instead of 'Alexander'.
        if arr1.dtype != StringDType():
            arr1 = arr1.astype(str)
        arr1 = arr1.astype(StringDType())
        if arr2.dtype != StringDType():
            arr2 = arr2.astype(str)
        arr2 = arr2.astype(StringDType())

    return arr1, arr2


def compare_arbors(a1, a2, groups=None, fields=None, skip1=1, skip2=1):
    """
    Compare all fields for all trees in two arbors.
    """

    if groups is None:
        groups = ["tree", "prog"]

    if fields is None:
        fields = a1.field_list

    for i, field in enumerate(fields):
        c1, c2 = get_stringsafe_compare_arrays(a1[field][::skip1], a2[field][::skip2])
        mylog.info(f"Comparing arbor field: {field} ({i + 1}/{len(fields)}).")
        assert_array_equal(c1, c2, err_msg=f"Arbor field mismatch: {a1, a2, field}.")

    trees1 = list(a1[::skip1])
    trees2 = list(a2[::skip2])

    ntot = len(trees1)
    pbar = get_pbar("Comparing trees", ntot)
    for i, (t1, t2) in enumerate(zip(trees1, trees2)):
        compare_trees(t1, t2, groups=groups, fields=fields)
        pbar.update(i + 1)
    pbar.finish()


def compare_trees(t1, t2, groups=None, fields=None):
    """
    Compare all fields between two trees.
    """

    if groups is None:
        groups = ["tree", "prog"]

    if fields is None:
        fields = t1.arbor.field_list

    for field in fields:
        for group in groups:
            c1, c2 = get_stringsafe_compare_arrays(t1[group, field], t2[group, field])
            assert_array_equal(
                c1, c2, err_msg=f"Tree comparison failed for {group} field: {field}."
            )
    t1.arbor.reset_node(t1)
    t2.arbor.reset_node(t2)


def compare_hdf5(fh1, fh2, compare=None, compare_groups=True, **kwargs):
    """
    Compare all datasets between two hdf5 files.
    """

    if compare is None:
        compare = assert_array_equal
    if not isinstance(fh1, h5py.Group):
        fh1 = h5py.File(fh1, "r")
    if not isinstance(fh2, h5py.Group):
        fh2 = h5py.File(fh2, "r")

    if compare_groups:
        err_msg = f"{fh1.file.filename} and {fh2.file.filename} have different datasets in group {fh1.name}."
        assert_equal(
            sorted(list(fh1.keys())), sorted(list(fh2.keys())), err_msg=err_msg
        )

    for key in fh1.keys():
        if isinstance(fh1[key], h5py.Group):
            compare_hdf5(
                fh1[key],
                fh2[key],
                compare_groups=compare_groups,
                compare=compare,
                **kwargs,
            )
        else:
            err_msg = (
                f"{key} field not equal for {fh1.file.filename} and {fh2.file.filename}"
            )
            if fh1[key].dtype == "int":
                assert_array_equal(fh1[key][()], fh2[key][()], err_msg=err_msg)
            else:
                compare(fh1[key][()], fh2[key][()], err_msg=err_msg, **kwargs)


def assert_rel_equal(a1, a2, decimals, err_msg="", verbose=True):
    # We have nan checks in here because occasionally we have fields that get
    # weighted without non-zero weights.  I'm looking at you, particle fields!
    if isinstance(a1, np.ndarray):
        assert a1.size == a2.size
        # Mask out NaNs
        assert (np.isnan(a1) == np.isnan(a2)).all()
        a1[np.isnan(a1)] = 1.0
        a2[np.isnan(a2)] = 1.0
        # Mask out 0
        ind1 = np.array(np.abs(a1) < np.finfo(a1.dtype).eps)
        ind2 = np.array(np.abs(a2) < np.finfo(a2.dtype).eps)
        assert (ind1 == ind2).all()
        a1[ind1] = 1.0
        a2[ind2] = 1.0
    elif np.any(np.isnan(a1)) and np.any(np.isnan(a2)):
        return True
    if not isinstance(a1, np.ndarray) and a1 == a2 == 0.0:
        # NANS!
        a1 = a2 = 1.0
    return assert_almost_equal(
        np.array(a1) / np.array(a2), 1.0, decimals, err_msg=err_msg, verbose=verbose
    )


def assert_array_rel_equal(a1, a2, decimals=16, **kwargs):
    """
    Wraps assert_rel_equal with, but decimals is a keyword arg.
    """
    assert_rel_equal(a1, a2, decimals, **kwargs)


def verify_get_node(my_tree, n=3):
    """
    Unit tests for get_node.
    """
    for selector in ["forest", "tree", "prog"]:
        node_list = list(my_tree[selector])

        inodes = np.arange(len(node_list))
        gen = np.random.default_rng(847)
        gen.shuffle(inodes)

        for inode in inodes[:3]:
            my_node = my_tree.get_node(selector, inode)
            err_msg = f"get_node failed: {selector} " + f"with {str(my_tree.arbor)}."
            assert_equal(my_node.uid, node_list[inode].uid, err_msg=err_msg)

            if selector == "forest":
                err_msg = (
                    "get_node index is not tree_id for " + f"{str(my_tree.arbor)}."
                )
                assert_equal(my_node.tree_id, inode, err_msg=err_msg)


def verify_get_leaf_nodes(my_tree):
    """
    Unit tests for get_leaf_nodes.
    """
    for selector in ["forest", "tree", "prog"]:
        uids1 = np.array(
            [node.uid for node in my_tree.get_leaf_nodes(selector=selector)]
        )
        uids2 = np.array(
            [
                my_halo.uid
                for my_halo in my_tree[selector]
                if not list(my_halo.ancestors)
            ]
        )

        err_msg = f"get_leaf_nodes failure for {selector} in {my_tree.arbor}."
        assert_equal(uids1, uids2, err_msg=err_msg)


def verify_get_root_nodes(my_tree):
    """
    Unit tests for get_root_nodes.
    """

    root_nodes1 = list(my_tree.get_root_nodes())
    for root_node in root_nodes1:
        assert_equal(
            root_node["desc_uid"],
            -1,
            err_msg=f"In {my_tree.arbor}: {root_node} has "
            + f"desc_uid={root_node['desc_uid']}, but expected -1.",
        )

    root_nodes2 = [node for node in my_tree["forest"] if node.descendent is None]

    uids1 = np.sort([node.uid for node in root_nodes1])
    uids2 = np.sort([node.uid for node in root_nodes2])

    assert_array_equal(
        uids1, uids2, err_msg=f"get_root_nodes failure in {my_tree.arbor}."
    )
