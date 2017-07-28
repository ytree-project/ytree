import numpy as np
import os
import yt

from ytree.arbor.frontends.tree_farm import \
    TreeFarmArbor
from ytree.tree_farm import \
    TreeFarm
from ytree.utilities.testing import \
    requires_file, \
    save_and_compare, \
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


FOF20 = os.path.join(
    test_data_dir,
    "fof_subfind/groups_020/fof_subhalo_tab_020.0.hdf5")

FOF40 = os.path.join(
    test_data_dir,
    "fof_subfind/groups_040/fof_subhalo_tab_040.0.hdf5")

class TreeFarmTest(TempDirTest):
    @requires_file(FOF20)
    def test_tree_farm_descendents(self):
        ts = yt.DatasetSeries(
            os.path.join(test_data_dir, "fof_subfind/groups_02*/*.0.hdf5"))
        my_tree = TreeFarm(ts, setup_function=setup_ds)
        my_tree.set_selector("all")
        my_tree.trace_descendents(
            "Group", filename="my_descendents/",
            fields=["virial_radius"])

        a = ytree.load("my_descendents/fof_subhalo_tab_020.0.h5")
        assert isinstance(a, TreeFarmArbor)
        save_and_compare(a)

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
        a = ytree.load(tfn)
        assert isinstance(a, TreeFarmArbor)
        save_and_compare(a)
