"""
ArborArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py
import numpy as np

from yt.units.unit_registry import \
    UnitRegistry

from ytree.arbor.arbor import \
    Arbor
from ytree.arbor.frontends.arborarbor.fields import \
    ArborArborFieldInfo
from ytree.arbor.frontends.arborarbor.io import \
    ArborArborRootFieldIO, \
    ArborArborTreeFieldIO
from ytree.arbor.tree_node import \
    TreeNode
from ytree.utilities.io import \
    _hdf5_yt_attr

class ArborArbor(Arbor):
    """
    Class for Arbors created with ytree version 1.1.0 or earlier.
    """

    _field_info_class = ArborArborFieldInfo
    _root_field_io_class = ArborArborRootFieldIO
    _tree_field_io_class = ArborArborTreeFieldIO

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
        self.unit_registry.modify("h", self.hubble_constant)
        self.box_size = _hdf5_yt_attr(fh, "box_size",
                                      unit_registry=self.unit_registry)
        field_list = []
        fi = {}
        for field in fh["data"]:
            d = fh["data"][field]
            units = _hdf5_yt_attr(d, "units")
            if isinstance(units, bytes):
                units = units.decode("utf")
            if len(d.shape) > 1:
                for ax in "xyz":
                    my_field = "%s_%s" % (field, ax)
                    field_list.append(my_field)
                    fi[my_field] = {"vector": True,
                                    "units": units}
            else:
                field_list.append(field)
                fi[field] = {"units": units}
        fh.close()
        self.field_list = field_list
        self.field_info.update(fi)

    def _plant_trees(self):
        fh = h5py.File(self.filename, "r")
        uids    = fh["data"]["uid"].value.astype(np.int64)
        descids = fh["data"]["desc_id"].value.astype(np.int64)
        treeids = fh["data"]["tree_id"].value.astype(np.int64)
        fh.close()

        root_filter = descids == -1
        roots = uids[root_filter]
        ntrees = roots.size
        self._trees = np.empty(ntrees, dtype=np.object)
        for i, root in enumerate(roots):
            my_node     = TreeNode(root, arbor=self, root=True)
            my_node._fi = np.where(root == treeids)[0]
            my_node._tree_size = my_node._fi.size
            self._trees[i] = my_node
        self._field_cache = {}
        self._field_cache["uid"] = uids
        self._field_cache["desc_id"] = descids
        self._ri = np.where(root_filter)[0]

    def _setup_tree(self, tree_node):
        # skip if this is not a root or if already setup
        if self.is_setup(tree_node):
            return

        ifield = tree_node._fi
        tree_node._uids      = self._field_cache["uid"][ifield]
        tree_node._desc_uids = self._field_cache["desc_id"][ifield]

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have "arbor_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(".h5"):
            return False
        try:
            with h5py.File(fn, "r") as f:
                if "arbor_type" not in f.attrs:
                    return False
                if f.attrs["arbor_type"].astype(str) != "ArborArbor":
                    return False
        except BaseException:
            return False
        return True
