"""
Field detection classes



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from collections import defaultdict
import numpy as np

from ytree.utilities.exceptions import \
    ArborFieldNotFound, \
    ArborFieldDependencyNotFound

_selectors = ("forest", "tree", "prog")

class FieldDetector(defaultdict):
    """
    A fake field data container used to calculate dependencies.
    """
    def __init__(self, arbor, name=None):
        self.arbor = arbor
        self.name = name

    def __missing__(self, key):
        if key not in self.arbor.field_info:
            raise ArborFieldDependencyNotFound(
                self.name, key, self.arbor)
        fi = self.arbor.field_info[key]
        units = fi.get("units", "")
        if fi.get("vector_field", False):
            data = np.ones((1, 3))
        else:
            data = np.ones(1)
        self[key] = self.arbor.arr(data, units)
        return self[key]

class SelectionDetector(defaultdict):
    """
    A TreeNode-like object to test select_halos criteria.
    """
    def __init__(self, arbor):
        self.arbor = arbor
        self.selectors = []

    def _validate_key(self, key):
        if not isinstance(key, tuple) and len(key) != 2:
            raise ValueError(f"Invalid selection criteria: {key}.")

        selector, field = key

        if selector not in _selectors:
            raise ValueError(f"Selector must be one of {_selectors}: {selector}.")

        if field not in self.arbor.field_info:
            raise ArborFieldNotFound(field, self.arbor)

    def __missing__(self, key):
        self._validate_key(key)
        selector, field = key
        if selector not in self.selectors:
            self.selectors.append(selector)

        fi = self.arbor.field_info[field]
        units = fi.get("units", "")

        self[key] = self.arbor.arr(np.ones(1), units)
        return self[key]
