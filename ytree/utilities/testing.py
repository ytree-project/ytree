"""
testing utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py
import numpy as np
from numpy.testing import \
    assert_equal, \
    assert_almost_equal, \
    assert_array_equal
import os
import shutil
import sys
import tempfile
from unittest import \
    skipIf, TestCase
from yt.funcs import \
    get_pbar

from ytree.data_structures.load import \
    load
from ytree.frontends.ytree import \
    YTreeArbor
from ytree.utilities.loading import \
    get_path
from ytree.utilities.logger import \
    ytreeLogger as mylog

try:
    from mpi4py import MPI
except ModuleNotFoundError:
    MPI = None

generate_results = \
  int(os.environ.get("YTREE_GENERATE_TEST_RESULTS", 0)) == 1

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

class ParallelTest:
    base_filename = "tiny_ctrees/locations.dat"
    test_filename = "test_arbor/test_arbor.h5"
    test_script = None
    ncores = 4

    def check_values(self, arbor, my_args):
        group = my_args[1]
        assert_array_equal(arbor["test_field"], 2 * arbor["mass"])
        for tree in arbor:
            assert_array_equal(tree[group, "test_field"], 2 * tree[group, "mass"])

    @skipIf(MPI is None, "mpi4py not installed")
    def test_parallel(self):

        for i, my_args in enumerate(self.arg_sets):
            with self.subTest(i=i):

                args = [self.test_script, self.base_filename, self.test_filename] + \
                    [str(arg) for arg in my_args]
                comm = MPI.COMM_SELF.Spawn(sys.executable, args=args, maxprocs=self.ncores)
                comm.Disconnect()

                test_arbor = load(self.test_filename)
                self.check_values(test_arbor, my_args)

class ArborTest:
    """
    A battery of tests for all frontends.
    """

    arbor_type = None
    test_filename = None
    load_kwargs = None
    groups = ("tree", "prog")
    num_data_files = None
    tree_skip = 1

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
        return self._arbor

    def test_arbor_type(self):
        assert isinstance(self.arbor, self.arbor_type)

    def test_data_files(self):
        if self.num_data_files is None:
            return
        assert_equal(
            len(self.arbor.data_files), self.num_data_files,
            err_msg=f'Incorrect number of data files for {self.arbor}.')

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
            np.random.shuffle(ihalos)
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
        ts0 = len(list(t['tree']))
        f0 = dict((field, t['tree', field])
                  for field in ['uid', 'desc_uid'])

        assert self.arbor.is_setup(t)
        assert self.arbor.is_grown(t)

        self.arbor.reset_node(t)

        for attr in self.arbor._reset_attrs:
            assert getattr(t, attr) is None
        assert_equal(len(t.field_data), 0)
        assert not self.arbor.is_setup(t)
        assert not self.arbor.is_grown(t)

        assert_equal(
            len(list(t['tree'])), ts0,
            err_msg=f'Trees are not the same size after resetting for {self.arbor}.')

        for field in f0:
            assert_array_equal(
                t['tree', field], f0[field],
                err_msg=f"Tree field {field} not the same after resetting for {self.arbor}.")

    def test_reset_nonroot(self):
        t = self.arbor[0]
        node = list(t['tree'])[1]
        ts0 = len(list(node['tree']))
        f0 = dict((field, node['tree', field])
                  for field in ['uid', 'desc_uid'])

        self.arbor.reset_node(node)

        assert_equal(
            len(list(node['tree'])), ts0,
            err_msg=f'Trees are not the same size after resetting for {self.arbor}.')

        for field in f0:
            assert_array_equal(
                node['tree', field], f0[field],
                err_msg=f"Tree field {field} not the same after resetting for {self.arbor}.")

    def test_save_and_reload(self):
        save_and_compare(self.arbor, groups=self.groups, skip=self.tree_skip)

    def test_vector_fields(self):
        a = self.arbor
        t = a[0]
        for field in a.field_info.vector_fields:

            mylog.info(f"Comparing vector field: {field}.")
            magfield = np.sqrt((a[field]**2).sum(axis=1))
            assert_array_equal(a[f"{field}_magnitude"], magfield,
                               err_msg=f"Magnitude field incorrect: {field}.")

            for i, ax in enumerate("xyz"):
                assert_array_equal(
                    a[f"{field}_{ax}"], a[field][:, i],
                    err_msg=(f"Arbor vector field {field} does not match "
                             f"in dimension {i}."))

                assert_array_equal(
                    t[f"{field}_{ax}"], t[field][i],
                    err_msg=(f"Tree vector field {field} does not match "
                             f"in dimension {i}."))

                for group in ["prog", "tree"]:
                    assert_array_equal(
                        t[group, f"{field}_{ax}"], t[group, field][:, i],
                        err_msg=(f"{group} vector field {field} does not match "
                                 f"in dimension {i}."))

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

    np.random.seed(seed)
    itrees = np.arange(arbor.size)
    np.random.shuffle(itrees)
    for itree in itrees[:5]:
        yield arbor[itree]

def save_and_compare(arbor, skip=1, groups=None):
    """
    Check that arbor saves correctly.
    """

    if skip > 1:
        trees = list(arbor[::skip])
    else:
        trees = None

    fn = arbor.save_arbor(trees=trees)
    save_arbor = load(fn)
    assert isinstance(save_arbor, YTreeArbor)
    compare_arbors(save_arbor, arbor, groups=groups, skip2=skip)

def compare_arbors(a1, a2, groups=None, fields=None, skip1=1, skip2=1):
    """
    Compare all fields for all trees in two arbors.
    """

    if groups is None:
        groups = ["tree", "prog"]

    if fields is None:
        fields = a1.field_list

    for i, field in enumerate(fields):
        mylog.info(f"Comparing arbor field: {field} ({i+1}/{len(fields)}).")
        assert_array_equal(a1[field][::skip1], a2[field][::skip2],
                           err_msg=f"Arbor field mismatch: {a1, a2, field}.")

    trees1 = list(a1[::skip1])
    trees2 = list(a2[::skip2])

    ntot = len(trees1)
    pbar = get_pbar("Comparing trees", ntot)
    for i, (t1, t2) in enumerate(zip(trees1, trees2)):
        compare_trees(t1, t2, groups=groups, fields=fields)
        pbar.update(i+1)
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
            assert_array_equal(
                t1[group, field], t2[group, field],
                err_msg=f"Tree comparison failed for {group} field: {field}.")
    t1.arbor.reset_node(t1)
    t2.arbor.reset_node(t2)

def compare_hdf5(fh1, fh2, compare=None, compare_groups=True,
                 **kwargs):
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
        assert_equal(sorted(list(fh1.keys())), sorted(list(fh2.keys())), err_msg=err_msg)

    for key in fh1.keys():
        if isinstance(fh1[key], h5py.Group):
            compare_hdf5(fh1[key], fh2[key],
                         compare_groups=compare_groups,
                         compare=compare, **kwargs)
        else:
            err_msg = f"{key} field not equal for {fh1.file.filename} and {fh2.file.filename}"
            if fh1[key].dtype == "int":
                assert_array_equal(fh1[key][()], fh2[key][()],
                                   err_msg=err_msg)
            else:
                compare(fh1[key][()], fh2[key][()],
                        err_msg=err_msg, **kwargs)

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
        np.random.shuffle(inodes)

        for inode in inodes[:3]:
            my_node = my_tree.get_node(selector, inode)
            err_msg = f"get_node failed: {selector} " + \
              f"with {str(my_tree.arbor)}."
            assert_equal(my_node.uid, node_list[inode].uid, err_msg=err_msg)

            if selector == "forest":
                err_msg = "get_node index is not tree_id for " + \
                  f"{str(my_tree.arbor)}."
                assert_equal(my_node.tree_id, inode, err_msg=err_msg)

def verify_get_leaf_nodes(my_tree):
    """
    Unit tests for get_leaf_nodes.
    """
    for selector in ["forest", "tree", "prog"]:
        uids1 = np.array([node.uid for node in
                          my_tree.get_leaf_nodes(selector=selector)])
        uids2 = np.array([my_halo.uid for my_halo in my_tree[selector]
                          if not list(my_halo.ancestors)])

        err_msg=f"get_leaf_nodes failure for {selector} in {my_tree.arbor}."
        assert_equal(uids1, uids2, err_msg=err_msg)

def verify_get_root_nodes(my_tree):
    """
    Unit tests for get_root_nodes.
    """

    root_nodes1 = list(my_tree.get_root_nodes())
    for root_node in root_nodes1:
        assert_equal(root_node["desc_uid"], -1)

    root_nodes2 = [node for node in my_tree["forest"]
                    if node.descendent is None]

    uids1 = np.sort([node.uid for node in root_nodes1])
    uids2 = np.sort([node.uid for node in root_nodes2])

    assert_array_equal(
        uids1, uids2,
        err_msg=f"get_root_nodes failure in {my_tree.arbor}.")
