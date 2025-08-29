from ytree.data_structures.load import load as ytree_load
from ytree.frontends.treefrog import TreeFrogArbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class TreeFrogArborTest(TempDirTest, ArborTest):
    arbor_type = TreeFrogArbor
    test_filename = "treefrog/VELOCIraptor.tree.t4.0-131.walkabletree.sage.forestID.foreststats.hdf5"
    groups = ("forest", "tree", "prog")
    num_data_files = 1
    tree_skip = 1000

    @property
    def arbor(self):
        arbor = super().arbor
        if "mass" not in arbor.field_info:
            arbor.add_alias_field("mass", "Mass_200crit", units="Msun")
        return arbor

    def test_load_from_datafile(self):
        for df in self.arbor.data_files:
            new_arbor = ytree_load(df.filename)
            assert isinstance(new_arbor, self.arbor_type)
