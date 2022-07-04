"""
Gadget4Arbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import glob
import h5py
import numpy as np
import re

from yt.funcs import \
    get_pbar

from ytree.data_structures.arbor import \
    SegmentedArbor

from ytree.frontends.gadget4.fields import \
    Gadget4FieldInfo
from ytree.frontends.gadget4.io import \
    Gadget4DataFile, \
    Gadget4TreeFieldIO

class Gadget4Arbor(SegmentedArbor):
    """
    Arbors loaded from consistent-trees data converted into HDF5.
    """

    _suffix = ".hdf5"
    _data_file_class = Gadget4DataFile
    _field_info_class = Gadget4FieldInfo
    _tree_field_io_class = Gadget4TreeFieldIO

    def _get_data_files(self):
        files = [self.parameter_filename]
        self.data_files = [self._data_file_class(f) for f in files]

    def _parse_parameter_file(self):
        f = h5py.File(self.parameter_filename, mode='r')

        g = f["Header"]
        self._size = g.attrs["Ntrees_Total"]

        g = f["Parameters"]
        self.hubble_constant = g.attrs["HubbleParam"]
        self.omega_matter = g.attrs["Omega0"]
        self.omega_lambda = g.attrs["OmegaLambda"]
        self.box_size = self.quan(g.attrs["BoxSize"], "Mpc/h")
        
        self._redshifts = f["TreeTimes/Redshift"][()]
        self._times = f["TreeTimes/Time"][()]

        field_list = []
        if self._size == 0:
            field_list = []
            return

        g = f["TreeHalos"]
        for d in g:
            dshape = g[d].shape
            if len(dshape) == 1:
                field_list.append(d)
            else:
                field_list.extend(
                    [f"{d}_{i}" for i in range(dshape[1])])

        self.field_list = field_list
        fi = dict((field, {"source": "TreeHalos"}) for field in field_list)
        self.field_list.append("TreeID")
        fi["TreeID"] = {"Source": "TreeTable"}
        self.field_info.update(fi)

    def _plant_trees(self):
        if self.is_planted or self._size == 0:
            return

        c = 0
        pbar = get_pbar('Planting trees', self._size)
        for idf, data_file in enumerate(self.data_files):
            size = data_file.size
            istart = c
            iend = istart + size

            self._node_info['_fi'][istart:iend] = idf
            self._node_info['_si'][istart:iend] = data_file._file_offsets
            self._node_info['_tree_size'][istart:iend] = data_file._file_count
            self._node_info['uid'][istart:iend] = data_file._uids
            c += size
            pbar.update(c)
        pbar.finish()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Should be an hdf5 file with a few key attributes.
        """
        fn = args[0]

        if not h5py.is_hdf5(fn):
            return False

        attrs = ["Nhalos_ThisFile", "Nhalos_Total",
                 "Ntrees_ThisFile", "Ntrees_Total"]
        groups = ["TreeHalos", "TreeTable", "TreeTimes"]

        with h5py.File(fn, mode='r') as f:
            g = f["Header"]
            for attr in attrs:
                if attr not in g.attrs:
                    return False
            for group in groups:
                if group not in f:
                    return False
        return True
