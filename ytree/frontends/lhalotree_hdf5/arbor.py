"""
LHaloTreeHDF5Arbor class and member functions



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

from ytree.frontends.lhalotree_hdf5.fields import \
    LHaloTreeHDF5FieldInfo
from ytree.frontends.lhalotree_hdf5.io import \
    LHaloTreeHDF5DataFile, \
    LHaloTreeHDF5TreeFieldIO

class LHaloTreeHDF5Arbor(SegmentedArbor):
    """
    Arbors loaded from consistent-trees data converted into HDF5.
    """

    _suffix = ".hdf5"
    _data_file_class = LHaloTreeHDF5DataFile
    _field_info_class = LHaloTreeHDF5FieldInfo
    _tree_field_io_class = LHaloTreeHDF5TreeFieldIO

    def __init__(self, filename,
                 hubble_constant=1.0, box_size=None,
                 omega_matter=None, omega_lambda=None):
        self.hubble_constant = hubble_constant
        self.omega_matter = omega_matter
        self.omega_lambda = omega_lambda
        if box_size is not None:
            self.box_size = self.quan(box_size, "Mpc/h")
        super().__init__(filename)

    def _get_data_files(self):
        suffix = self._suffix
        reg = re.search(rf"^(.+\D)\d+{suffix}$", self.filename)
        if reg is None:
            raise RuntimeError(
                f"Cannot determine numbering system for {self.filename}.")
        prefix = reg.groups()[0]
        files = glob.glob(f"{prefix}*{self._suffix}")
        self.data_files = [self._data_file_class(f, self) for f in files]
        self._file_count = np.array([df._size for df in self.data_files])
        self._size = self._file_count.sum()

    def _parse_parameter_file(self):
        f = h5py.File(self.parameter_filename, mode='r')
        g = f["Header"]
        ntrees = g.attrs["NtreesPerFile"]
        self._redshifts = g["Redshifts"][()]

        field_list = []
        if ntrees == 0:
            field_list = []
            return

        g = f["Tree0"]
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
        fi["desc_uid"]["dependencies"] = ["Descendant"]
        self.field_info.update(fi)

    def _plant_trees(self):
        if self.is_planted or self._size == 0:
            return

        c = 0
        file_offsets = self._file_count.cumsum() - self._file_count
        pbar = get_pbar('Planting trees', self._size)
        for idf, data_file in enumerate(self.data_files):
            data_file.open()
            tree_size = data_file.fh["Header"]["TreeNHalos"][()]
            data_file.close()

            size = data_file._size
            istart = file_offsets[idf]
            iend = istart + size

            self._node_info['_fi'][istart:iend] = idf
            self._node_info['_si'][istart:iend] = np.arange(size)
            self._node_info['_tree_size'][istart:iend] = tree_size
            c += size
            pbar.update(c)
        pbar.finish()
        uids = self._node_info['_tree_size']
        self._node_info['uid'] = uids.cumsum() - uids

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Should be an hdf5 file with a few key attributes.
        """
        fn = args[0]

        if not h5py.is_hdf5(fn):
            return False

        attrs = ["FirstSnapshotNr", "LastSnapshotNr", "SnapSkipFac",
                 "NtreesPerFile", "NhalosPerFile", "ParticleMass"]
        groups = ["Redshifts", "TotNsubhalos", "TreeNHalos"]

        with h5py.File(fn, mode='r') as f:
            g = f["Header"]
            for attr in attrs:
                if attr not in g.attrs:
                    return False
            for group in groups:
                if group not in g:
                    return False
        return True
