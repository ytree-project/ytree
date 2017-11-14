"""
tests for LHaloTree reader.


"""

import os
import numpy as np
import nose.tools as nt
import ytree
from ytree.utilities.testing import \
    requires_file, \
    test_data_dir
from ytree.arbor.frontends.lhalotree import utils as lhtutils
from ytree.arbor.frontends.lhalotree.arbor import LHaloTreeArbor


MMT = os.path.join(test_data_dir, 'lhalotree', 'trees_063.1')
MMP = os.path.join(test_data_dir, 'lhalotree', 'millennium.param')
CTT = os.path.join(test_data_dir, 'consistent_trees', 'tree_0_0_0.dat')


@requires_file(MMT)
def test_read_header_default():
    header_size, nhalos_per_tree = lhtutils.read_header_default(MMT)


@requires_file(MMT)
def test_LHaloTreeReader():
    reader = lhtutils.LHaloTreeReader(MMT)
    attr_list = ['filename', 'fileindex', 'filepattern',
                 'parameter_file', 'scale_factor_file', 'header_size',
                 'nhalos_per_tree', 'nhalos_before_tree', 'totnhalos',
                 'ntrees', 'item_dtype', 'raw_fields', 'add_fields', 'fields',
                 'treenum_arr', 'mmap', 'filenum', 'all_uids', 'all_desc_uids',
                 '_root_data',
                 'hubble_constant', 'omega_matter', 'omega_lambda', 'box_size',
                 'periodic', 'comoving', 'units_vel', 'units_len', 'units_mass',
                 'scale_factors', 'parameters']
    for a in attr_list:
        getattr(reader, a)
    # fd = reader.open()
    for i in range(reader.ntrees):
        tree = reader.read_single_tree(i, validate=True)  # , fd=fd)
        root = reader.read_single_root(i, validate=True)  # , fd=fd)
        halo = reader.read_single_halo(i, 0, validate=True)  # , fd=fd)
    # fd.close()


@requires_file(CTT)
def test_fail_load():
    assert(not LHaloTreeArbor._is_valid(CTT))

        
@requires_file(MMT)
@requires_file(MMP)
def test_load():
    a = ytree.load(MMT, parameter_file=MMP)
    print(a.size)
    print(a[0]["tree"])
    print(a[0]["tree", "mass"])
    print(a.trees)
