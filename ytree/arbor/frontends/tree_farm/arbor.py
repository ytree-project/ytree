"""
TreeFarmArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from collections import \
    defaultdict
import glob
import h5py

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
    _hdf5_yt_attr, \
    parse_h5_attr

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
            parse_h5_attr(fh, "unit_registry_json"))
        right = _hdf5_yt_attr(fh, "domain_right_edge",
                              unit_registry=my_ur)
        left  = _hdf5_yt_attr(fh, "domain_left_edge",
                              unit_registry=my_ur)
        # Drop the "cm" suffix because all lengths will
        # be in comoving units.
        self.box_size = self.quan(
            (right - left)[0].to("Mpccm/h"), "Mpc/h")
        fh.close()

    def _get_data_files(self):
        prefix = self.filename.rsplit("_", 1)[0] + "_"
        files = glob.glob("%s*%s" % (prefix, self._suffix))
        suffix = ".0" + self._suffix
        fids = defaultdict(list)
        for my_file in files:
            fid = int(my_file[len(prefix):-len(suffix)])
            fids[fid].append(my_file)
        my_files = [fids[myfid]
                    for myfid in sorted(fids.keys(), reverse=True)]
        self.data_files = [[self._data_file_class(f, self)
                            for f in fl] for fl in my_files]

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have a "data_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(self._suffix):
            return False
        try:
            with h5py.File(fn, "r") as f:
                if "data_type" not in f.attrs:
                    return False
                if f.attrs["data_type"].astype(str) != "halo_catalog":
                    return False
        except BaseException:
            return False
        return True
