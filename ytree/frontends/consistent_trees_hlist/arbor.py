"""
ConsistentTreesHlistArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import glob
import os

from ytree.frontends.consistent_trees_hlist.io import \
    ConsistentTreesHlistDataFile
from ytree.frontends.consistent_trees.fields import \
    ConsistentTreesFieldInfo
from ytree.frontends.consistent_trees.arbor import \
    ConsistentTreesArbor
from ytree.frontends.rockstar.arbor import \
    RockstarArbor

class ConsistentTreesHlistArbor(RockstarArbor):
    """
    Class for Arbors created from consistent-trees hlist_*.list files.

    This is a hybrid type with multiple catalog files like the rockstar
    frontend, but with headers structured like consistent-trees.
    """

    _has_uids = True
    _field_info_class = ConsistentTreesFieldInfo
    _data_file_class = ConsistentTreesHlistDataFile
    _parse_parameter_file = ConsistentTreesArbor._parse_parameter_file

    def _get_data_files(self):
        """
        Get all out_*.list files and sort them in reverse order.
        """
        prefix = os.path.join(os.path.dirname(self.filename), "hlist_")
        suffix = ".list"
        my_files = glob.glob("%s*%s" % (prefix, suffix))

        # sort by catalog number
        my_files.sort(
            key=lambda x:
            self._get_file_index(x, prefix, suffix),
            reverse=True)
        self.data_files = \
          [self._data_file_class(f, self) for f in my_files]

    def _get_file_index(self, f, prefix, suffix):
        return float(f[f.find(prefix)+len(prefix):f.rfind(suffix)])

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .list.
        """
        fn = args[0]
        if not os.path.basename(fn).startswith("hlist") or \
          not fn.endswith(".list"):
            return False
        return True
