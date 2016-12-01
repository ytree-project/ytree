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
TF25 = os.path.join(
    get_test_data_dir(),
    "/Users/britton/EnzoRuns/ytree_test_data/100Mpc_64/dm_gadget/data",
    "groups_025/fof_subhalo_tab_025.0.hdf5")

@in_tmpdir
@requires_file(TF16)
@requires_file(TF25)
def test_treefarm():
    fns = os.path.join(
        get_test_data_dir(),
        "100Mpc_64/dm_gadget/data/groups_*/*.0.hdf5")
    ts = yt.DatasetSeries(fns)

    my_tree = TreeFarm(ts, setup_function=setup_ds)
    my_tree.trace_descendents(
        "Group", fields=["virial_radius"],
        filename="all_halos/")

    a1 = load("all_halos/fof_subhalo_tab_016.0.hdf5.0.h5")
    assert isinstance(a1, TreeFarmArbor)
    m1 = a1["particle_mass"]

    fn = a1.save_arbor("arbor_tf.h5")
    a2 = load(fn)
    assert isinstance(a2, ArborArbor)
    m2 = a2["particle_mass"]

    assert (m1 == m2).all()
    compare_arbors(a1, a2)

    i1 = np.argsort(m1.d)[::-1][0]
    fn = a1[i1].save_tree()
    a3 = load(fn)
    assert isinstance(a3, ArborArbor)
    for field in a1.field_list:
        assert (a1[i1]["tree", field] == a3[0]["tree", field]).all()

    ds = yt.load(TF25)
    i_max = np.argmax(ds.r["Group", "particle_mass"].d)
    my_ids = ds.r["Group", "particle_identifier"][i_max]
    my_tree.trace_ancestors("Group", my_ids,
                            filename="my_halos/",
                            fields=["virial_radius"])
    a4 = load("my_halos/fof_subhalo_tab_025.0.hdf5.0.h5")
    assert isinstance(a4, TreeFarmArbor)
    for field in a4.field_list:
        if field in ["uid", "desc_id"]: continue
        assert (a3[0]["line", field] == a4[0]["line", field]).all()
