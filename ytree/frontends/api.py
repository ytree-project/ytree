"""
API for ytree frontends



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import importlib

_frontends = [
    "ahf",
    "consistent_trees",
    "consistent_trees_hdf5",
    "lhalotree",
    "lhalotree_hdf5",
    "moria",
    "rockstar",
    "treefarm",
    "treefrog",
    "ytree",
]

class _frontend_container:
    def __init__(self):
        for frontend in _frontends:
            _mod = f"ytree.frontends.{frontend}"
            setattr(self, frontend, importlib.import_module(_mod))
        setattr(self, 'api', importlib.import_module('ytree.frontends.api'))
        setattr(self, '__name__', 'ytree.frontends.api')
