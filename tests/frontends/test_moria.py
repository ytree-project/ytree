import h5py
import numpy as np
from numpy.testing import assert_array_equal

from ytree.frontends.moria import MoriaArbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class MoriaArborTest(TempDirTest, ArborTest):
    arbor_type = MoriaArbor
    test_filename = "moria/moria_tree_testsim050.hdf5"
    groups = ("forest", "tree", "prog")
    num_data_files = 1
    tree_skip = 100

    @property
    def arbor(self):
        arbor = super().arbor
        if "mass" not in arbor.field_info:
            arbor.add_alias_field("mass", "Mpeak", units="Msun")
        return arbor

    def test_missing_descuids(self):
        a = self.arbor
        a._plant_trees()

        fh = h5py.File(self.arbor.parameter_filename, mode="r")
        dids = fh["descendant_id"][()]
        ids = fh["id"][()]
        dindex = fh["descendant_index"][()]
        missing = np.setdiff1d(dids, ids)

        for my_desc in missing:
            if my_desc == -1:
                continue

            index = np.where(dids == my_desc)
            my_id = ids[index][0]
            my_dindex = (index[0] + 1, dindex[index][0])

            ai = np.digitize(dindex[index][0], a._node_info["_si"]) - 1
            t = a[ai]
            inode = t["forest", "uid"] == my_id
            assert_array_equal(t["forest", "desc_uid"][inode], ids[my_dindex])
