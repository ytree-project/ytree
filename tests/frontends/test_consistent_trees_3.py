from ytree.frontends.consistent_trees import ConsistentTreesHlistArbor
from ytree.testing.arbor_test import ArborTest
from ytree.testing.utilities import TempDirTest


class ConsistentTreesHlistArborTest(TempDirTest, ArborTest):
    arbor_type = ConsistentTreesHlistArbor
    test_filename = "ctrees_hlists/hlists/hlist_0.12521.list"
    num_data_files = 10
    tree_skip = 100
