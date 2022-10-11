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
    Gadget4 inline merger tree format.
    """

    _suffix = ".hdf5"
    _data_file_class = Gadget4DataFile
    _field_info_class = Gadget4FieldInfo
    _tree_field_io_class = Gadget4TreeFieldIO
    _node_io_attrs = ("_fi", "_si", "_fei", "_ei")

    def _get_data_files(self):
        if self._nfiles == 1:
            files = [self.parameter_filename]
        else:
            suffix = self._suffix
            reg = re.search(rf"^(.+\D)\d+{suffix}$", self.parameter_filename)
            if reg is None:
                raise RuntimeError(
                    f"Cannot determine numbering system for {self.filename}.")
            prefix = reg.groups()[0]
            files = [f"{prefix}{i}{suffix}" for i in range(self._nfiles)]

        self.data_files = [self._data_file_class(f) for f in files]

    def _parse_parameter_file(self):
        f = h5py.File(self.parameter_filename, mode="r")

        g = f["Header"]
        self._size = int(g.attrs["Ntrees_Total"])
        self._nfiles = int(g.attrs["NumFiles"])

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
        fi = dict((field, {}) for field in field_list)
        for field in ["uid", "desc_uid"]:
            self.field_list.append(field)
            fi[field] = {"units": "", "source": "arbor"}
        fi["desc_uid"]["dependencies"] = ["TreeDescendant"]
        self.field_info.update(fi)

    def _plant_trees(self):
        if self.is_planted or self._size == 0:
            return

        istart = 0
        file_sizes = np.empty(len(self.data_files), dtype=int)
        offset = np.empty(self._size, dtype=int)
        pbar = get_pbar("Planting trees", self._size)
        for idf, data_file in enumerate(self.data_files):
            file_sizes[idf] = data_file.nnodes
            ntrees = data_file.ntrees
            iend = istart + ntrees
            my_slice = slice(istart, iend)

            if ntrees > 0:
                self._node_info["_fi"][my_slice] = idf
                self._node_info["_tree_size"][my_slice] = data_file.tree_sizes
                offset[my_slice] = data_file.offsets

            istart += ntrees
            pbar.update(iend)

        file_end_offset = file_sizes.cumsum()
        file_start_offset = file_end_offset - file_sizes
        tree_size = self._node_info["_tree_size"]
        file_start_index = np.digitize(offset, file_end_offset)
        file_end_index = np.digitize(offset+tree_size, file_end_offset, right=True)

        self._node_info["_fi"] = file_start_index
        self._node_info["_fei"] = file_end_index
        self._node_info["_si"] = offset - file_start_offset[file_start_index]
        self._node_info["_ei"] = offset + tree_size - file_start_offset[file_end_index]
        self._node_info["uid"] = offset
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
                 "Ntrees_ThisFile", "Ntrees_Total",
                 "NumFiles"]
        groups = ["TreeHalos", "TreeTable", "TreeTimes"]

        with h5py.File(fn, mode="r") as f:
            g = f["Header"]
            for attr in attrs:
                if attr not in g.attrs:
                    return False
            for group in groups:
                if group not in f:
                    return False
        return True
