from ytree.frontends.csv import \
    CSVArbor
from ytree.utilities.testing import \
    ArborTest, \
    TempDirTest

class CSVArborTest(TempDirTest, ArborTest):
    arbor_type = CSVArbor
    test_filename = "csv/trees.csv"

    def load_callback(self, a):
        a.set_selector("max_field_value", "charisma")
