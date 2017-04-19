"""
YTreeArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py

from yt.arbor.arbor import \
    MonolithArbor

class ArborArbor(MonolithArbor):
    """
    Class for Arbors created from the :func:`~ytree.arbor.Arbor.save_arbor`
    or :func:`~ytree.tree_node.TreeNode.save_tree` functions.
    """
    def _load_field_data(self):
        """
        All data stored in a single hdf5 file.  Get cosmological
        parameters and modify unit registry for hubble constant.
        """
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
        self._field_data = dict([(f, _hdf5_yt_array(fh["data"], f, self))
                                 for f in fh["data"]])
        fh.close()

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
                if f.attrs["arbor_type"].astype(str) != "ArborArbor":
                    return False
        except:
            return False
        return True
