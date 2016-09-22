import os
from yt.testing import \
    requires_file
from ytree import \
    load_arbor
from ytree.config import \
    ytreecfg
from ytree.utilities.testing import \
    compare_arbors, \
    in_tmpdir

test_data_dir = ytreecfg["ytree"].get("test_data_dir", ".")
RS0 = os.path.join(test_data_dir,
                   "100Mpc_64/dm_enzo/rockstar_halos/out_0.list")

@in_tmpdir
@requires_file(RS0)
def test_rs_arbor():
    a1 = load_arbor(os.path.join(test_data_dir, RS0), "Rockstar")
    m1 = a1.arr([t["mvir"] for t in a1.trees])

    fn = a1.save_arbor("arbor_rs.h5")
    a2 = load_arbor(fn, "Arbor")
    m2 = a2.arr([t["mvir"] for t in a2.trees])

    assert (m1 == m2).all()
    compare_arbors(a1, a2)
