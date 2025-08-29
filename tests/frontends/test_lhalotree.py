"""
tests for LHaloTree reader.


"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from numpy.testing import assert_equal
import numpy as np
import os
import tempfile
import ytree
from ytree.frontends.lhalotree import LHaloTreeArbor, utils as lhtutils
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest, requires_file
from ytree.utilities.loading import test_data_dir


MMT = os.path.join(test_data_dir, "lhalotree", "trees_063.0")
SMT = os.path.join(test_data_dir, "lhalotree", "small_trees_063.0")
MMP = os.path.join(test_data_dir, "lhalotree", "millennium.param")
CTT = os.path.join(test_data_dir, "consistent_trees", "tree_0_0_0.dat")


class LHaloTreeArborTest(TempDirTest, ArborTest):
    arbor_type = LHaloTreeArbor
    test_filename = "lhalotree/trees_063.0"
    groups = ("forest", "tree", "prog")
    tree_skip = 100


@requires_file(MMT)
def make_small_example(ntrees_per_file=None):
    if ntrees_per_file is None:
        ntrees_per_file = np.array([2, 2], "int")
    ntrees_before_file = np.cumsum(ntrees_per_file) - ntrees_per_file
    header_size0, nhalos_per_tree0 = lhtutils.read_header_default(MMT)
    data0 = lhtutils._read_from_mmap(
        MMT,
        header_size=header_size0,
        nhalo=np.sum(nhalos_per_tree0[: np.sum(ntrees_per_file)]),
    )
    fname_base = os.path.splitext(SMT)[0]
    prev_halos = 0
    for i in range(len(ntrees_per_file)):
        ifile = f"{fname_base}.{i}"
        start_tree = ntrees_before_file[i]
        stop_tree = start_tree + ntrees_per_file[i]
        nhalos_per_tree1 = nhalos_per_tree0[start_tree:stop_tree]
        ntothalos1 = np.sum(nhalos_per_tree1)
        data1 = data0[prev_halos : (prev_halos + ntothalos1)]
        prev_halos += ntothalos1
        header_size1 = lhtutils.save_header_default(ifile, nhalos_per_tree1)
        lhtutils._save_to_mmap(ifile, data1, header_size=header_size1)


@requires_file(SMT)
def test_io_header_default():
    header_size0, nhalos_per_tree0 = lhtutils.read_header_default(SMT)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        _header_size = lhtutils.save_header_default(tmp, nhalos_per_tree0)
        assert_equal(_header_size, header_size0)
        tmp.close()
        header_size1, nhalos_per_tree1 = lhtutils.read_header_default(tmp.name)
        os.remove(tmp.name)
    assert_equal(header_size1, header_size0)
    np.testing.assert_array_equal(nhalos_per_tree1, nhalos_per_tree0)


@requires_file(SMT)
def test_io_mmap():
    header_size0, nhalos_per_tree0 = lhtutils.read_header_default(SMT)
    data0 = lhtutils._read_from_mmap(SMT, header_size=header_size0)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.close()
        lhtutils._save_to_mmap(tmp.name, data0)
        data1 = lhtutils._read_from_mmap(tmp.name)
        os.remove(tmp.name)
    np.testing.assert_array_equal(data1, data0)


@requires_file(SMT)
def test_io_file():
    header_size0, nhalos_per_tree0 = lhtutils.read_header_default(SMT)
    data0 = lhtutils._read_from_file(SMT, header_size=header_size0)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.close()
        lhtutils._save_to_file(tmp.name, data0)
        data1 = lhtutils._read_from_file(tmp.name)
        os.remove(tmp.name)
    np.testing.assert_array_equal(data1, data0)


@requires_file(SMT)
def test_io_trees_default():
    header_size0, nhalos_per_tree0 = lhtutils.read_header_default(SMT)
    data0 = lhtutils.read_trees_default(SMT, header_size=header_size0)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.close()
        lhtutils.save_trees_default(tmp.name, data0)
        data1 = lhtutils.read_trees_default(tmp.name)
        os.remove(tmp.name)
    for k in data0.keys():
        assert k in data1
        np.testing.assert_array_equal(data1[k], data0[k])


@requires_file(SMT)
def test_LHaloTreeReader():
    reader = lhtutils.LHaloTreeReader(SMT)
    attr_list = [
        "filename",
        "fileindex",
        "filepattern",
        "parameter_file",
        "scale_factor_file",
        "header_size",
        "nhalos_per_tree",
        "nhalos_before_tree",
        "totnhalos",
        "ntrees",
        "item_dtype",
        "raw_fields",
        "add_fields",
        "fields",
        "treenum_arr",
        "fobj",
        "filenum",
        "all_uids",
        "all_desc_uids",
        "_root_data",
        "hubble_constant",
        "omega_matter",
        "omega_lambda",
        "box_size",
        "periodic",
        "comoving",
        "units_vel",
        "units_len",
        "units_mass",
        "scale_factors",
        "parameters",
    ]
    for a in attr_list:
        getattr(reader, a)
    # fd = reader.open()
    for i in range(reader.ntrees):
        reader.read_single_tree(i, validate=True)  # , fd=fd)
        reader.read_single_root(i, validate=True)  # , fd=fd)
        reader.read_single_halo(i, 0, validate=True)  # , fd=fd)
    # fd.close()


@requires_file(CTT)
def test_fail_load():
    assert not LHaloTreeArbor._is_valid(CTT)


@requires_file(SMT)
@requires_file(MMP)
def test_load():
    a = ytree.load(SMT, parameter_file=MMP)
    print(a.size)
    print(a[0]["tree"])
    print(a[0]["tree", "mass"])
    print(a.trees)
