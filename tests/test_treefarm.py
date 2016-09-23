import numpy as np
import os
import yt

from yt.testing import \
    requires_file
from ytree.arbor import \
    ArborArbor, \
    TreeFarmArbor, \
    load
from ytree.tree_farm import \
    TreeFarm
from ytree.utilities.testing import \
    compare_arbors, \
    get_test_data_dir, \
    in_tmpdir

def virial_radius(field, data):
    rho_c = data.ds.cosmology.critical_density(data.ds.current_redshift)
    return (3 * data["particle_mass"] /
            (800 * np.pi * rho_c))**(1./3)

def setup_ds(ds):
    for ftype in ds.particle_type_counts:
        if ds.particle_type_counts[ftype] == 0: continue
        ds.add_field((ftype, "virial_radius"),
                     function=virial_radius,
                     units="cm", particle_type=True)

TF16 = os.path.join(
    get_test_data_dir(),
    "/Users/britton/EnzoRuns/ytree_test_data/100Mpc_64/dm_gadget/data",
    "groups_016/fof_subhalo_tab_016.0.hdf5")

@in_tmpdir
@requires_file(TF16)
def test_treefarm_forward():
    fns = os.path.join(
        get_test_data_dir(),
        "100Mpc_64/dm_gadget/data/groups_*/*.0.hdf5")
    ts = yt.DatasetSeries(fns)

    my_tree = TreeFarm(ts, setup_function=setup_ds)
    my_tree.trace_descendents(
        "Group", halo_properties=["virial_radius"],
        filename="all_halos/")

    a1 = load("all_halos/fof_subhalo_tab_016.0.hdf5.0.h5")
    assert isinstance(a1, TreeFarmArbor)
    m1 = a1.arr([t["particle_mass"] for t in a1.trees])

    fn = a1.save_arbor("arbor_tf.h5")
    a2 = load(fn)
    assert isinstance(a2, ArborArbor)
    m2 = a2.arr([t["particle_mass"] for t in a2.trees])

    assert (m1 == m2).all()

    compare_arbors(a1, a2)

    i1 = np.argsort(m1.d)[::-1][0]
    fn = a1.trees[i1].save_tree()
    a3 = load(fn)
    assert isinstance(a3, ArborArbor)
    for field in a1._field_data:
        assert (a1.trees[i1].tree(field) == a3.trees[0].tree(field)).all()
