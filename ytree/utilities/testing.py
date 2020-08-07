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
    assert_array_equal
import os
import shutil
import tempfile
from unittest import \
    TestCase
from yt.testing import \
    assert_rel_equal
from yt.funcs import \
    get_pbar

from ytree.data_structures.load import \
    load
from ytree.frontends.ytree import \
    YTreeArbor
from ytree.utilities.loading import \
    check_path

generate_results = \
  int(os.environ.get("YTREE_GENERATE_TEST_RESULTS", 0)) == 1

def requires_file(req_file):

    def ffalse(func):
        return None

    def ftrue(func):
        return func

    if not isinstance(req_file, list):
        req_file = [req_file]
    for fn in req_file:
        if not os.path.exists(fn):
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

class ArborTest:
    """
    Do some standard tests on an arbor.
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
                self.test_filename = check_path(self.test_filename)
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
            err_msg='Incorrect number of data files for %s.' % self.arbor)

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
        assert_equal(len(t._field_data), 0)
        assert not self.arbor.is_setup(t)
        assert not self.arbor.is_grown(t)

        assert_equal(
            len(list(t['tree'])), ts0,
            err_msg='Trees are not the same size after resetting for %s.' %
            self.arbor)

        for field in f0:
            assert_array_equal(
                t['tree', field], f0[field],
                err_msg='Tree field %s not the same after resetting for %s.' %
                (field, self.arbor))

    def test_reset_nonroot(self):
        t = self.arbor[0]
        node = list(t['tree'])[1]
        ts0 = len(list(node['tree']))
        f0 = dict((field, node['tree', field])
                  for field in ['uid', 'desc_uid'])

        self.arbor.reset_node(node)

        assert_equal(
            len(list(node['tree'])), ts0,
            err_msg='Trees are not the same size after resetting for %s.' %
            self.arbor)

        for field in f0:
            assert_array_equal(
                node['tree', field], f0[field],
                err_msg='Tree field %s not the same after resetting for %s.' %
                (field, self.arbor))

    def test_save_and_reload(self):
        save_and_compare(self.arbor, groups=self.groups, skip=self.tree_skip)

    def test_vector_fields(self):
        a = self.arbor
        t = a[0]
        for field in a.field_info.vector_fields:

            magfield = np.sqrt((a[field]**2).sum(axis=1))
            assert_array_equal(a["%s_magnitude" % field], magfield)

            for i, ax in enumerate("xyz"):
                assert_array_equal(
                    a["%s_%s" % (field, ax)],
                    a[field][:, i])

                assert_array_equal(
                    t["%s_%s" % (field, ax)],
                    t[field][i])

                for group in ["prog", "tree"]:
                    assert_array_equal(
                        t[group, "%s_%s" % (field, ax)],
                        t[group, field][:, i])

def save_and_compare(arbor, skip=1, groups=None):
    """
    Check that arbor saves correctly.
    """

    if skip > 1:
        trees = arbor[::skip]
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

    for field in fields:
        assert (a1[field][::skip1] == a2[field][::skip2]).all()

    trees1 = a1[::skip1]
    trees2 = a2[::skip2]

    ntot = trees1.size
    pbar = get_pbar("Comparing trees", ntot)
    for t1, t2 in zip(trees1, trees2):
        compare_trees(t1, t2, groups=groups, fields=fields)
        pbar.update(1)
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
                err_msg="Tree comparison failed for %s field: %s." %
                (group, field))
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
        assert sorted(list(fh1.keys())) == sorted(list(fh2.keys())), \
          "%s and %s have different datasets in group %s." % \
          (fh1.file.filename, fh2.file.filename, fh1.name)

    for key in fh1.keys():
        if isinstance(fh1[key], h5py.Group):
            compare_hdf5(fh1[key], fh2[key],
                         compare_groups=compare_groups,
                         compare=compare, **kwargs)
        else:
            err_msg = "%s field not equal for %s and %s" % \
              (key, fh1.file.filename, fh2.file.filename)
            if fh1[key].dtype == "int":
                assert_array_equal(fh1[key][()], fh2[key][()],
                                   err_msg=err_msg)
            else:
                compare(fh1[key][()], fh2[key][()],
                        err_msg=err_msg, **kwargs)

def assert_array_rel_equal(a1, a2, decimals=16, **kwargs):
    """
    Wraps assert_rel_equal with, but decimals is a keyword arg.
    """
    assert_rel_equal(a1, a2, decimals, **kwargs)
