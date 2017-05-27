"""
YTreeArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016-2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py
import json
import numpy as np

from yt.frontends.ytdata.utilities import \
    _hdf5_yt_array
from yt.units.unit_registry import \
    UnitRegistry

from ytree.arbor.arbor import \
    MonolithArbor
from ytree.arbor.tree_node import \
    TreeNode
from ytree.utilities.io import \
    _hdf5_yt_attr

class YTreeArbor(MonolithArbor):
    """
    Class for Arbors created from the :func:`~ytree.arbor.Arbor.save_arbor`
    or :func:`~ytree.tree_node.TreeNode.save_tree` functions.
    """

    def _parse_parameter_file(self):
        fh = h5py.File(self.filename, "r")
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            setattr(self, attr, fh.attrs[attr])
        if "unit_registry_json" in fh.attrs:
            self.unit_registry = \
              UnitRegistry.from_json(
                  fh.attrs["unit_registry_json"].astype(str))
        self.box_size = _hdf5_yt_attr(fh, "box_size",
                                      unit_registry=self.unit_registry)
        self.field_info.update(json.loads(fh.attrs["field_info"]))
        fh.close()

    def _plant_trees(self):
        fh = h5py.File(self.filename, "r")
        ntrees = fh.attrs["total_trees"]
        uids = fh["root"]["id"].value.astype(np.int64)
        fh.close()

        self._trees = np.empty(ntrees, dtype=np.object)
        for i in range(ntrees):
            self._trees[i] = TreeNode(uids[i], arbor=self, root=True)

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have "arbor_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(".h5"): return False
        try:
            with h5py.File(fn, "r") as f:
                if "arbor_type" not in f.attrs:
                    return False
                if f.attrs["arbor_type"].astype(str) != "YTreeArbor":
                    return False
        except:
            return False
        return True
