"""
Arbor field-related classes



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

class FieldInfoContainer(dict):
    alias_fields = ()
    def __init__(self, arbor):
        self.arbor = arbor

    def setup_aliases(self):
        for alias in self.alias_fields:
            self.arbor.add_alias_field(
                alias[0], alias[1], units=alias[2])

    def setup_derived_fields(self):
        def _redshift(data):
            return 1. / data["scale_factor"] - 1.
        self.arbor.add_derived_field(
            "redshift", _redshift, units="", force_add=False)

class FieldContainer(dict):
    def __init__(self, arbor):
        self.arbor = arbor

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
