import numpy as np
import os
from yt.testing import \
    requires_file
from ytree.arbor import \
    ArborArbor, \
    RockstarArbor, \
    load
from ytree.utilities.testing import \
    compare_arbors, \
    get_test_data_dir, \
    in_tmpdir

RS0 = os.path.join(get_test_data_dir(),
                   "100Mpc_64/dm_enzo/rockstar_halos/out_0.list")

@in_tmpdir
@requires_file(RS0)
def test_rs_arbor():
    a1 = load(RS0)
    assert isinstance(a1, RockstarArbor)
    m1 = a1["mvir"]

    fn = a1.save_arbor("arbor_rs.h5")
    a2 = load(fn)
    assert isinstance(a2, ArborArbor)
    m2 = a2["mvir"]

    assert (m1 == m2).all()
    compare_arbors(a1, a2)

    i1 = np.argsort(m1.d)[::-1][0]
    fn = a1[i1].save_tree()
    a3 = load(fn)
    assert isinstance(a3, ArborArbor)
    for field in a1.field_list:
        assert (a1[i1]["tree", field] == a3[0]["tree", field]).all()
