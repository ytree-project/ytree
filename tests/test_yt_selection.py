"""
tests for yt frontend and selection functions



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import numpy as np
from numpy.testing import assert_raises
import ytree

from ytree.testing.utilities import TempDirTest, assert_array_rel_equal, requires_file
from ytree.yt_frontend import YTreeDataset

CTG = "tiny_ctrees/locations.dat"


class YTSelectionTest(TempDirTest):
    """
    Test class for selecting halos with yt.
    """

    _setup = False

    def setUp(self):
        super().setUp()
        self._setup = True

    _arbor = None

    @property
    def arbor(self):
        if not self._setup:
            return
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
            ytree_data = np.concatenate([t["forest", field] for t in a])
            ytree_data.sort()
            assert_array_rel_equal(yt_data, ytree_data, decimals=5)

    @requires_file(CTG)
    def test_yt_sphere(self):
        a = self.arbor
        ds = a.ytds

        sp = ds.sphere(0.5 * ds.domain_center, (20, "Mpc/h"))

        ytree_pos = np.concatenate([t["forest", "position"] for t in a])
        ytree_mass = np.concatenate([t["forest", "mass"] for t in a])
        r = a.quan(sp.radius.to("unitary"))
        c = a.arr(sp.center.to("unitary"))
        ytree_r = np.sqrt(((ytree_pos - c) ** 2).sum(axis=1))
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

    @requires_file(CTG)
    def test_above(self):
        a = self.arbor
        ds = a.ytds

        mt = 1e10
        sel = a.get_yt_selection(above=[("mass", mt, "Msun")])
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass >= mt).all()
        sel_mass.sort()

        ad = ds.all_data()
        ad_mass = ad["halos", "mass"].to("Msun")
        yt_mass = ad_mass[ad_mass >= mt]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_above_no_units(self):
        a = self.arbor
        ds = a.ytds

        mt = 1e10
        sel = a.get_yt_selection(above=[("mass", mt)])
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass >= mt).all()
        sel_mass.sort()

        ad = ds.all_data()
        ad_mass = ad["halos", "mass"].to("Msun")
        yt_mass = ad_mass[ad_mass >= mt]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_above_sphere(self):
        a = self.arbor
        ds = a.ytds
        sp = ds.sphere(0.5 * ds.domain_center, (20, "Mpc/h"))

        mt = 1e10
        sel = a.get_yt_selection(above=[("mass", mt, "Msun")], data_source=sp)
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass >= mt).all()
        sel_mass.sort()

        sp_mass = sp["halos", "mass"].to("Msun")
        yt_mass = sp_mass[sp_mass >= mt]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_below(self):
        a = self.arbor
        ds = a.ytds

        mt = 1e10
        sel = a.get_yt_selection(below=[("mass", mt, "Msun")])
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass <= mt).all()
        sel_mass.sort()

        ad = ds.all_data()
        ad_mass = ad["halos", "mass"].to("Msun")
        yt_mass = ad_mass[ad_mass <= mt]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_below_no_units(self):
        a = self.arbor
        ds = a.ytds

        mt = 1e10
        sel = a.get_yt_selection(below=[("mass", mt)])
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass <= mt).all()
        sel_mass.sort()

        ad = ds.all_data()
        ad_mass = ad["halos", "mass"].to("Msun")
        yt_mass = ad_mass[ad_mass <= mt]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_below_sphere(self):
        a = self.arbor
        ds = a.ytds
        sp = ds.sphere(0.5 * ds.domain_center, (20, "Mpc/h"))

        mt = 1e10
        sel = a.get_yt_selection(below=[("mass", mt, "Msun")], data_source=sp)
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass <= mt).all()
        sel_mass.sort()

        sp_mass = sp["halos", "mass"].to("Msun")
        yt_mass = sp_mass[sp_mass <= mt]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_about(self):
        a = self.arbor
        ds = a.ytds

        mt = 1e10
        within = 0.5
        sel = a.get_yt_selection(about=[("mass", mt, "Msun", within)])
        sel_mass = sel["halos", "mass"].to("Msun")
        assert ((sel_mass >= (1 - within) * mt) & (sel_mass <= (1 + within) * mt)).all()
        sel_mass.sort()

        ad = ds.all_data()
        ad_mass = ad["halos", "mass"].to("Msun")
        yt_mass = ad_mass[
            (ad_mass >= (1 - within) * mt) & (ad_mass <= (1 + within) * mt)
        ]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_about_no_units(self):
        a = self.arbor
        ds = a.ytds

        mt = 1e10
        within = 0.5
        sel = a.get_yt_selection(about=[("mass", mt, within)])
        sel_mass = sel["halos", "mass"].to("Msun")
        assert ((sel_mass >= (1 - within) * mt) & (sel_mass <= (1 + within) * mt)).all()
        sel_mass.sort()

        ad = ds.all_data()
        ad_mass = ad["halos", "mass"].to("Msun")
        yt_mass = ad_mass[
            (ad_mass >= (1 - within) * mt) & (ad_mass <= (1 + within) * mt)
        ]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_about_sphere(self):
        a = self.arbor
        ds = a.ytds
        sp = ds.sphere(0.5 * ds.domain_center, (20, "Mpc/h"))

        mt = 1e10
        within = 0.5
        sel = a.get_yt_selection(about=[("mass", mt, within)], data_source=sp)
        sel_mass = sel["halos", "mass"].to("Msun")
        assert ((sel_mass >= (1 - within) * mt) & (sel_mass <= (1 + within) * mt)).all()
        sel_mass.sort()

        sp_mass = sp["halos", "mass"].to("Msun")
        yt_mass = sp_mass[
            (sp_mass >= (1 - within) * mt) & (sp_mass <= (1 + within) * mt)
        ]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_equal(self):
        a = self.arbor
        ds = a.ytds

        sel = a.get_yt_selection(equal=[("mmp?", 1, "")])
        sel_mmp = sel["halos", "mmp?"].to("")
        assert (sel_mmp == 1).all()
        sel_mmp.sort()

        ad = ds.all_data()
        ad_mmp = ad["halos", "mmp?"].to("")
        yt_mmp = ad_mmp[ad_mmp == 1]
        yt_mmp.sort()
        assert_array_rel_equal(sel_mmp, yt_mmp, decimals=5)

    @requires_file(CTG)
    def test_equal_no_units(self):
        a = self.arbor
        ds = a.ytds

        sel = a.get_yt_selection(equal=[("mmp?", 1)])
        sel_mmp = sel["halos", "mmp?"].to("")
        assert (sel_mmp == 1).all()
        sel_mmp.sort()

        ad = ds.all_data()
        ad_mmp = ad["halos", "mmp?"].to("")
        yt_mmp = ad_mmp[ad_mmp == 1]
        yt_mmp.sort()
        assert_array_rel_equal(sel_mmp, yt_mmp, decimals=5)

    @requires_file(CTG)
    def test_equal_sphere(self):
        a = self.arbor
        ds = a.ytds
        sp = ds.sphere(0.5 * ds.domain_center, (20, "Mpc/h"))

        sel = a.get_yt_selection(equal=[("mmp?", 1, "")], data_source=sp)
        sel_mmp = sel["halos", "mmp?"].to("")
        assert (sel_mmp == 1).all()
        sel_mmp.sort()

        sp_mmp = sp["halos", "mmp?"].to("")
        yt_mmp = sp_mmp[sp_mmp == 1]
        yt_mmp.sort()
        assert_array_rel_equal(sel_mmp, yt_mmp, decimals=5)

    @requires_file(CTG)
    def test_conditionals(self):
        a = self.arbor
        ds = a.ytds

        sel = a.get_yt_selection(conditionals=['obj["halos", "mass"] > 1e10'])
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass >= 1e10).all()
        sel_mass.sort()

        ad = ds.all_data()
        ad_mass = ad["halos", "mass"].to("Msun")
        yt_mass = ad_mass[ad_mass >= 1e10]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_conditionals_sphere(self):
        a = self.arbor
        ds = a.ytds
        sp = ds.sphere(0.5 * ds.domain_center, (20, "Mpc/h"))

        sel = a.get_yt_selection(
            conditionals=['obj["halos", "mass"] > 1e10'], data_source=sp
        )
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass >= 1e10).all()
        sel_mass.sort()

        sp_mass = sp["halos", "mass"].to("Msun")
        yt_mass = sp_mass[sp_mass >= 1e10]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_yt_selection_bad_input(self):
        a = self.arbor

        with assert_raises(ValueError):
            a.get_yt_selection(
                conditionals=['obj["halos", "mass"] > 1e10'], above=["mass", 1e10]
            )

    @requires_file(CTG)
    def test_multiple_criteria_1(self):
        a = self.arbor
        ds = a.ytds

        sel = a.get_yt_selection(above=[("mass", 1e10, "Msun"), ("redshift", 0.5)])
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass >= 1e10).all()
        sel_redshift = sel["halos", "redshift"]
        assert (sel_redshift >= 0.5).all()
        sel_mass.sort()

        ad = ds.all_data()
        ad_mass = ad["halos", "mass"].to("Msun")
        ad_redshift = ad["halos", "redshift"]
        yt_mass = ad_mass[(ad_mass >= 1e10) & (ad_redshift >= 0.5)]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_multiple_criteria_2(self):
        a = self.arbor
        ds = a.ytds

        sel = a.get_yt_selection(
            above=[("mass", 1e10, "Msun")], below=[("redshift", 0.5)]
        )
        sel_mass = sel["halos", "mass"].to("Msun")
        assert (sel_mass >= 1e10).all()
        sel_redshift = sel["halos", "redshift"]
        assert (sel_redshift <= 0.5).all()
        sel_mass.sort()

        ad = ds.all_data()
        ad_mass = ad["halos", "mass"].to("Msun")
        ad_redshift = ad["halos", "redshift"]
        yt_mass = ad_mass[(ad_mass >= 1e10) & (ad_redshift <= 0.5)]
        yt_mass.sort()
        assert_array_rel_equal(sel_mass, yt_mass, decimals=5)

    @requires_file(CTG)
    def test_nodes_from_sphere(self):
        a = self.arbor
        ds = a.ytds
        sp = ds.sphere(0.5 * ds.domain_center, (20, "Mpc/h"))

        nodes = list(a.get_nodes_from_selection(sp))

        sp_mass = sp["halos", "mass"].to("Msun")
        sp_mass.sort()
        node_mass = a.arr([node["mass"] for node in nodes])
        node_mass.sort()
        assert_array_rel_equal(node_mass, sp_mass, decimals=5)

        node_pos = a.arr([node["position"] for node in nodes])
        r = a.quan(sp.radius.to("unitary"))
        c = a.arr(sp.center.to("unitary"))
        node_r = np.sqrt(((node_pos - c) ** 2).sum(axis=1))
        assert (node_r <= r).all()

    @requires_file(CTG)
    def test_nodes_from_selection(self):
        a = self.arbor

        sel = a.get_yt_selection(above=[("mass", 1e10, "Msun")])
        sel_mass = sel["halos", "mass"].to("Msun")
        sel_mass.sort()

        nodes = list(a.get_nodes_from_selection(sel))
        node_mass = a.arr([node["mass"] for node in nodes]).to("Msun")
        node_mass.sort()

        assert_array_rel_equal(node_mass, sel_mass, decimals=5)
