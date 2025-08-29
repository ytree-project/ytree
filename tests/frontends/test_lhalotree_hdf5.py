from ytree.data_structures.load import load as ytree_load
from ytree.frontends.lhalotree_hdf5 import LHaloTreeHDF5Arbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class LHaloTreeHDF5ArborTest(TempDirTest, ArborTest):
    arbor_type = LHaloTreeHDF5Arbor
    test_filename = "TNG50-4-Dark/trees_sf1_099.0.hdf5"
    load_kwargs = {
        "box_size": 35,
        "hubble_constant": 0.6774,
        "omega_matter": 0.3089,
        "omega_lambda": 0.6911,
    }
    groups = ("forest", "tree", "prog")
    num_data_files = 7
    tree_skip = 100

    @property
    def arbor(self):
        arbor = super().arbor
        if "mass" not in arbor.field_info:
            arbor.add_alias_field("mass", "Group_M_TopHat200", units="Msun")
        return arbor

    def test_load_without_kwargs(self):
        filename = self.arbor.filename
        a = ytree_load(filename)
        a.save_arbor()
