"""
TreeFarmArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016-2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import glob
import h5py
import numpy as np

from yt.units.unit_registry import \
    UnitRegistry

from ytree.arbor.arbor import \
    CatalogArbor
from ytree.arbor.frontends.tree_farm.fields import \
    TreeFarmFieldInfo
from ytree.arbor.frontends.tree_farm.io import \
    TreeFarmDataFile, \
    TreeFarmTreeFieldIO
from ytree.utilities.io import \
    _hdf5_yt_attr

class TreeFarmArbor(CatalogArbor):
    """
    Class for Arbors created with :class:`~ytree.tree_farm.TreeFarm`.
    """

    _suffix = ".h5"
    _field_info_class = TreeFarmFieldInfo
    _tree_field_io_class = TreeFarmTreeFieldIO
    _data_file_class = TreeFarmDataFile

    def _parse_parameter_file(self):
        fh = h5py.File(self.filename, "r")

        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            setattr(self, attr, fh.attrs[attr])

        my_ur = UnitRegistry.from_json(
            fh.attrs["unit_registry_json"])
        right = _hdf5_yt_attr(fh, "domain_right_edge",
                              unit_registry=my_ur)
        left  = _hdf5_yt_attr(fh, "domain_left_edge",
                              unit_registry=my_ur)
        # Drop the "cm" suffix because all lengths will
        # be in comoving units.
        self.box_size = self.quan(
            (right - left)[0].to("Mpccm/h"), "Mpc/h")

        fields = list(fh.keys())
        fi = {}
        for field in fields:
            units = fh[field].attrs["units"]
            if isinstance(units, bytes):
                units = units.decode("utf")
            fi[field] = {"source": "file", "units": units}

        fields.append("redshift")
        fi["redshift"] = {"source": "header", "units": ""}

        self.field_list = fields
        self.field_info.update(fi)
        self._get_data_files()

    def _get_file_index(self, f, prefix, suffix):
        return int(f[f.find(prefix)+len(prefix)+1:f.find(".0")])

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have a "data_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(".h5"): return False
        try:
            with h5py.File(fn, "r") as f:
                if "data_type" not in f.attrs:
                    return False
                if f.attrs["data_type"].astype(str) != "halo_catalog":
                    return False
        except:
            return False
        return True
