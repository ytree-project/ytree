"""
tests for yt frontend and selection functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
from unyt import uconcatenate
import ytree

from ytree.utilities.testing import \
    TempDirTest, \
    assert_array_rel_equal, \
    requires_file
from ytree.yt_frontend import YTreeDataset

CTG = "tiny_ctrees/locations.dat"

class YTSelectionTest(TempDirTest):

    _arbor = None
    @property
    def arbor(self):
        if self._arbor is not None:
            return self._arbor

        a = ytree.load(CTG)
        fn = a.save_arbor()
        self._arbor = ytree.load(fn)
        return self._arbor

    @requires_file(CTG)
    def test_yt_all_data(self):
        a = self.arbor
        ds = a.ytds
        assert isinstance(ds, YTreeDataset)

        ad = ds.all_data()
        for field, units in zip(["mass", "redshift"], ["Msun", ""]):
            yt_data = ad["halos", field].to(units)
            yt_data.sort()
            ytree_data = uconcatenate([t["forest", field] for t in a])
            ytree_data.sort()
            assert_array_rel_equal(yt_data, ytree_data, decimals=5)

    @requires_file(CTG)
    def test_yt_sphere(self):
        a = self.arbor
        ds = a.ytds
        assert isinstance(ds, YTreeDataset)

        sp = ds.sphere(0.5*ds.domain_center, (20, "Mpc/h"))

        ytree_pos = uconcatenate([t["forest", "position"] for t in a])
        ytree_mass = uconcatenate([t["forest", "mass"] for t in a])
        r = a.quan(sp.radius.to("unitary"))
        c = a.arr(sp.center.to("unitary"))
        ytree_r = np.sqrt(((ytree_pos - c)**2).sum(axis=1))
        in_sphere = ytree_r <= r

        ytree_sp_r = ytree_r[in_sphere].to("unitary")
        ytree_sp_r.sort()
        sp_r = sp["halos", "particle_radius"].to("unitary")
        sp_r.sort()
        assert_array_rel_equal(ytree_sp_r, sp_r, decimals=5)

        sp_mass = sp["halos", "mass"].to("Msun")
        sp_mass.sort()
        ytree_sp_mass = ytree_mass[in_sphere].to("Msun")
        ytree_sp_mass.sort()
        assert_array_rel_equal(ytree_sp_mass, sp_mass, decimals=5)
