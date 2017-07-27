import numpy as np
import os
import yt

from ytree.arbor.frontends.ytree import \
    YTreeArbor
from ytree.arbor.frontends.tree_farm import \
    TreeFarmArbor
from ytree.tree_farm import \
    TreeFarm
from ytree.utilities.testing import \
    compare_arbors, \
    requires_file, \
    test_data_dir, \
    TempDirTest

import ytree

def virial_radius(field, data):
    rho_c = data.ds.cosmology.critical_density(
        data.ds.current_redshift)
    return (3 * data["particle_mass"] /
            (800 * np.pi * rho_c))**(1./3)

def setup_ds(ds):
    for ftype in ds.particle_type_counts:
        if ds.particle_type_counts[ftype] == 0: continue
        ds.add_field((ftype, "virial_radius"),
                     function=virial_radius,
                     units="cm", particle_type=True)


TFD = os.path.join(
    test_data_dir,
    "tree_farm_descendents/fof_subhalo_tab_000.0.h5")

TFA = os.path.join(
    test_data_dir,
    "tree_farm_ancestors/fof_subhalo_tab_017.0.h5")

FOF20 = os.path.join(
    test_data_dir,
    "fof_subfind/groups_020/fof_subhalo_tab_020.0.hdf5")

FOF40 = os.path.join(
    test_data_dir,
    "fof_subfind/groups_040/fof_subhalo_tab_040.0.hdf5")

class TreeFarmTest(TempDirTest):
    @requires_file(TFD)
    def test_tree_farm_arbor_descendents(self):
        a1 = ytree.load(TFD)
        assert isinstance(a1, TreeFarmArbor)
        m1 = a1["mass"]

        fn = a1.save_arbor("arbor_tfd")
        a2 = ytree.load(fn)
        assert isinstance(a2, YTreeArbor)
        m2 = a2["mass"]

        assert (m1 == m2).all()
        for gtype in ["tree", "prog"]:
            compare_arbors(a2, a1, group=gtype)

    @requires_file(TFA)
    def test_tree_farm_arbor_ancestors(self):
        a1 = ytree.load(TFA)
        assert isinstance(a1, TreeFarmArbor)
        m1 = a1["mass"]

        fn = a1.save_arbor("arbor_tfa")
        a2 = ytree.load(fn)
        assert isinstance(a2, YTreeArbor)
        m2 = a2["mass"]

        assert (m1 == m2).all()
        for gtype in ["tree", "prog"]:
            compare_arbors(a2, a1, group=gtype)

    @requires_file(FOF20)
    def test_tree_farm_descendents(self):
        ts = yt.DatasetSeries(
            os.path.join(test_data_dir, "fof_subfind/groups_02*/*.0.hdf5"))
        my_tree = TreeFarm(ts, setup_function=setup_ds)
        my_tree.set_selector("all")
        my_tree.trace_descendents(
            "Group", filename="my_descendents/",
            fields=["virial_radius"])

        a1 = ytree.load("my_descendents/fof_subhalo_tab_020.0.h5")
        assert isinstance(a1, TreeFarmArbor)
        m1 = a1["mass"]

        fn = a1.save_arbor("arbor_tfd")
        a2 = ytree.load(fn)
        assert isinstance(a2, YTreeArbor)
        m2 = a2["mass"]

        assert (m1 == m2).all()
        for gtype in ["tree", "prog"]:
            compare_arbors(a2, a1, group=gtype)

    @requires_file(FOF40)
    def test_tree_farm_ancestors(self):
        ts = yt.DatasetSeries(
            os.path.join(test_data_dir, "fof_subfind/groups_04*/*.0.hdf5"))

        ds = yt.load(ts.outputs[-1])
        ad = ds.all_data()
        mw = ad["Group", "particle_mass"] > ds.quan(1e14, "Msun")
        mw_ids = ad["Group", "particle_identifier"][mw].d.astype(np.int64)

        my_tree = TreeFarm(ts, setup_function=setup_ds)
        my_tree.set_ancestry_filter("most_massive")
        my_tree.set_ancestry_short("above_mass_fraction", 0.5)
        my_tree.set_selector("all")
        my_tree.trace_ancestors(
            "Group", mw_ids, filename="my_ancestors/",
            fields=["virial_radius"])

        tfn = os.path.join("my_ancestors/%s.0.h5" % str(ds))
        a1 = ytree.load(tfn)
        assert isinstance(a1, TreeFarmArbor)
        m1 = a1["mass"]

        fn = a1.save_arbor("arbor_tfd")
        a2 = ytree.load(fn)
        assert isinstance(a2, YTreeArbor)
        m2 = a2["mass"]

        assert (m1 == m2).all()
        for gtype in ["tree", "prog"]:
            compare_arbors(a2, a1, group=gtype)

    #     i1 = np.argsort(m1.d)[::-1][0]
    #     fn = a1[i1].save_tree()
    #     a3 = load(fn)
    #     assert isinstance(a3, ArborArbor)
    #     for field in a1.field_list:
    #         assert (a1[i1]["tree", field] == a3[0]["tree", field]).all()

    #     ds = yt.load(TF25)
    #     i_max = np.argmax(ds.r["Group", "particle_mass"].d)
    #     my_ids = ds.r["Group", "particle_identifier"][i_max]
    #     my_tree.trace_ancestors("Group", my_ids,
    #                             filename="my_halos/",
    #                             fields=["virial_radius"])
    #     a4 = load("my_halos/fof_subhalo_tab_025.0.h5")
    #     assert isinstance(a4, TreeFarmArbor)
    #     for field in a4.field_list:
    #         if field in ["uid", "desc_id"]: continue
    #         assert (a3[0]["line", field] == a4[0]["line", field]).all()
