import os
from yt.testing import \
    requires_file
from ytree import \
    load
from ytree.utilities.testing import \
    compare_arbors, \
    get_test_data_dir, \
    in_tmpdir

CT = os.path.join(get_test_data_dir(),
                  "100Mpc_64/dm_enzo/rockstar_halos/trees/tree_0_0_0.dat")

@in_tmpdir
@requires_file(CT)
def test_ct_arbor():
    a1 = load(CT, "ConsistentTrees")
    m1 = a1.arr([t["mvir"] for t in a1.trees])

    fn = a1.save_arbor("arbor_ct.h5")
    a2 = load(fn, "Arbor")
    m2 = a2.arr([t["mvir"] for t in a2.trees])

    assert (m1 == m2).all()
    compare_arbors(a1, a2)
