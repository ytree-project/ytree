"""
miscellaneous utility tests



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016-2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os
import ytree

from ytree.utilities.testing import \
    requires_file, \
    test_data_dir

CT = os.path.join(test_data_dir, "consistent_trees/tree_0_0_0.dat")

@requires_file(CT)
def test_select_halos():
    a = ytree.load(CT)

    halos = a.select_halos('tree["tree", "Orig_halo_ID"] == 0')
    hids = a.arr([h["Orig_halo_ID"] for h in halos])
    assert (hids == 0).all()

    halos = a.select_halos('tree["prog", "Orig_halo_ID"] == 0',
                           select_from="prog")
    hids = a.arr([h["Orig_halo_ID"] for h in halos])
    assert (hids == 0).all()

    # test that we catch criteria/select_from mismatch
    try:
        halos = a.select_halos('tree["tree", "Orig_halo_ID"] == 0',
                               select_from="prog")
    except RuntimeError:
        pass
    except BaseException:
        assert False
    else:
        assert False
