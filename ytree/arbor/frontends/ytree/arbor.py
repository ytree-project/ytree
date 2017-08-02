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

from yt.units.unit_registry import \
    UnitRegistry

from ytree.arbor.arbor import \
    Arbor
from ytree.arbor.frontends.ytree.io import \
    YTreeRootFieldIO, \
    YTreeTreeFieldIO
from ytree.arbor.tree_node import \
    TreeNode
from ytree.utilities.io import \
    _hdf5_yt_attr, \
    parse_h5_attr

class YTreeArbor(Arbor):
    """
    Class for Arbors created from the
    :func:`~ytree.arbor.arbor.Arbor.save_arbor`
    or :func:`~ytree.arbor.tree_node.TreeNode.save_tree` functions.
    """
    _root_field_io_class = YTreeRootFieldIO
    _tree_field_io_class = YTreeTreeFieldIO
    _suffix = ".h5"

    def _node_io_loop(self, func, *args, **kwargs):
        root_nodes = kwargs.pop("root_nodes", None)
        if root_nodes is None:
            root_nodes = self.trees
        opbar = kwargs.pop("pbar", None)

        ai = np.array([node._ai for node in root_nodes])
        dfi = np.digitize(ai, self._ei)
        udfi = np.unique(dfi)

        for i in udfi:
            if opbar is not None:
                kwargs["pbar"] = "%s [%d/%d]" % (opbar, i+1, udfi.size)
            my_nodes = root_nodes[dfi == i]
            kwargs["root_nodes"] = my_nodes
            kwargs["fcache"] = {}

            fn = "%s_%04d%s" % (self._prefix, i, self._suffix)
            f = h5py.File(fn, "r")
            kwargs["f"] = f
            super(YTreeArbor, self)._node_io_loop(func, *args, **kwargs)
            f.close()

    def _parse_parameter_file(self):
        self._prefix = \
          self.filename[:self.filename.rfind(self._suffix)]
        fh = h5py.File(self.filename, "r")
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            setattr(self, attr, fh.attrs[attr])
        if "unit_registry_json" in fh.attrs:
            self.unit_registry = \
              UnitRegistry.from_json(
                  parse_h5_attr(fh, "unit_registry_json"))
        self.box_size = _hdf5_yt_attr(
            fh, "box_size", unit_registry=self.unit_registry)
        self.field_info.update(
            json.loads(parse_h5_attr(fh, "field_info")))
        self.field_list = list(self.field_info.keys())
        fh.close()

    def _plant_trees(self):
        fh = h5py.File(self.filename, "r")
        ntrees   = fh.attrs["total_trees"]
        uids     = fh["data"]["uid"].value.astype(np.int64)
        self._si = fh["index"]["tree_start_index"].value
        self._ei = fh["index"]["tree_end_index"].value
        fh.close()

        self._trees = np.empty(ntrees, dtype=np.object)
        for i in range(ntrees):
            my_node        = TreeNode(uids[i], arbor=self, root=True)
            my_node._ai    = i
            self._trees[i] = my_node

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have "arbor_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(self._suffix):
            return False
        try:
            with h5py.File(fn, "r") as f:
                if "arbor_type" not in f.attrs:
                    return False
                if f.attrs["arbor_type"].astype(str) != "YTreeArbor":
                    return False
        except:
            return False
        return True
