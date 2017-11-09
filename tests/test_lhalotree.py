"""
tests for LHaloTree reader.


"""


import numpy as np
import nose.tools as nt
from ytree.utilities.testing import \
    requires_file, \
    test_data_dir
from ytree.arbor.frontends.lhalotree import utils as lhtutils

MM = '/root/ytree/ytree/trees_063.0'


@requires_file(MM)
def test_read_header_default():
    header_size, nhalos_per_tree = lhtutils.read_header_default(MM)


@requires_file(MM)
def test_LHaloTreeReader():
    reader = lhtutils.LHaloTreeReader(MM)
    for i in range(reader.ntrees):
        tree = reader.read_single_lhalotree(i)
            
