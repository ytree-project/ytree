"""
Arbor fields



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from collections import \
    defaultdict
import numpy as np

from ytree.utilities.exceptions import \
    ArborFieldDependencyNotFound

class FakeFieldContainer(defaultdict):
    def __init__(self, arbor, name=None):
        self.arbor = arbor
        self.name = name

    def __missing__(self, key):
        if key not in self.arbor.field_info:
            raise ArborFieldDependencyNotFound(
                self.name, key, self.arbor)
        units = self.arbor.field_info[key].get("units", "")
        self[key] = self.arbor.arr(np.ones(1), units)
        return self[key]
