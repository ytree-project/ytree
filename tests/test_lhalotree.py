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


MMT = os.path.join(test_data_dir, 'lhalotree', 'trees_063.3')


@requires_file(MMT)
def test_read_header_default():
    header_size, nhalos_per_tree = lhtutils.read_header_default(MMT)


@requires_file(MMT)
def test_LHaloTreeReader():
    reader = lhtutils.LHaloTreeReader(MMT)
    for i in range(reader.ntrees):
        tree = reader.read_single_lhalotree(i)
        
@requires_file(MMT)
def test_load():
    a = ytree.load(MMT)
    print(a.size)
    print(a[0]["tree"])
    print(a[0]["tree", "mass"])
    print(a.trees)
