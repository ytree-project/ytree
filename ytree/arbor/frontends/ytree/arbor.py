"""
YTreeArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
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
    YTreeDataFile, \
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

    def _node_io_loop_prepare(self, root_nodes):
        ai = np.array([node._ai for node in root_nodes])
        dfi = np.digitize(ai, self._node_io._ei)
        udfi = np.unique(dfi)
        data_files = [self._node_io.data_files[i] for i in udfi]
        node_list = [root_nodes[dfi == i] for i in udfi]
        return data_files, node_list

    def _node_io_loop_start(self, data_file):
        data_file._field_cache = {}
        data_file.open()

    def _node_io_loop_finish(self, data_file):
        data_file._field_cache = {}
        data_file.close()

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
        self._node_io._si = fh["index"]["tree_start_index"].value
        self._node_io._ei = fh["index"]["tree_end_index"].value
        fh.close()

        self._node_io.data_files = \
          [YTreeDataFile("%s_%04d%s" % (self._prefix, i, self._suffix))
           for i in range(self._node_io._si.size)]

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
        except BaseException:
            return False
        return True
