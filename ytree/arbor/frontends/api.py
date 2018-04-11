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
    "arborarbor",
    "consistent_trees",
    "lhalotree",
    "rockstar",
    "tree_farm",
    "ytree",
]

class _frontend_container:
    def __init__(self):
        for frontend in _frontends:
            _mod = "ytree.arbor.frontends.%s" % frontend
            setattr(self, frontend, importlib.import_module(_mod))
        setattr(self, 'api', importlib.import_module('ytree.arbor.frontends.api'))
        setattr(self, '__name__', 'ytree.arbor.frontends.api')
