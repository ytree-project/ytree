"""
ConsistentTreesHlistArbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os

from ytree.frontends.rockstar.io import \
    RockstarDataFile

class ConsistentTreesHlistDataFile(RockstarDataFile):
    def _parse_header(self):
        super(ConsistentTreesHlistDataFile, self)._parse_header()

        prefix = os.path.join(os.path.dirname(self.filename), "hlist_")
        suffix = ".list"
        self.scale_factor = self.arbor._get_file_index(
            self.filename, prefix, suffix)
