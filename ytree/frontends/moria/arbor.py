"""
MoriaArbor class and member functions



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
    Arbor

from ytree.frontends.moria.fields import \
    MoriaFieldInfo
from ytree.frontends.moria.io import \
    MoriaDataFile, \
    MoriaTreeFieldIO

class MoriaArbor(Arbor):
    """
    Arbors loaded from consistent-trees data converted into HDF5.
    """

    _suffix = ".hdf5"
    _data_file_class = MoriaDataFile
    _field_info_class = MoriaFieldInfo
    _tree_field_io_class = MoriaTreeFieldIO
    _node_io_attrs = ('_fi', '_si')

    def _parse_parameter_file(self):
        f = h5py.File(self.parameter_filename, mode='r')
        g = f["simulation"]
        self.hubble_constant = float(g.attrs['cosmo_h'])
        self.omega_matter = g.attrs['cosmo_Omega_m']
        self.omega_lambda = g.attrs['cosmo_Omega_L']
        self.omega_radiation = g.attrs['cosmo_Omega_r']
        self.box_size = self.quan(g.attrs['box_size'], 'Mpc/h')
        self._redshifts = g.attrs['snap_z']
        self._scale_factors = g.attrs['snap_a']
        self._times = self.arr(g.attrs['snap_t'], 'Gyr')

        field_list = []
        fi = {}
        for field in f:
            if isinstance(f[field], h5py.Group):
                continue
            if len(f[field].shape) == 3:
                fields = [f"{field}_{i}" for i in range(f[field].shape[2])]
                field_list.extend(fields)
                fi.update({myf: {"vector": True} for myf in fields})
            else:
                field_list.append(field)
                fi[field] = {}
        f.close()

        self.field_list = field_list
        self.field_info.update(fi)

    # def _plant_trees(self):
    #     if self.is_planted or self._size == 0:
    #         return

    #     c = 0
    #     file_offsets = self._file_count.cumsum() - self._file_count
    #     pbar = get_pbar('Planting trees', self._size)
    #     for idf, data_file in enumerate(self.data_files):
    #         data_file.open()
    #         tree_size = data_file.fh["Header"]["TreeNHalos"][()]
    #         data_file.close()

    #         size = data_file._size
    #         istart = file_offsets[idf]
    #         iend = istart + size

    #         self._node_info['_fi'][istart:iend] = idf
    #         self._node_info['_si'][istart:iend] = np.arange(size)
    #         self._node_info['_tree_size'][istart:iend] = tree_size
    #         c += size
    #         pbar.update(c)
    #     pbar.finish()
    #     uids = self._node_info['_tree_size']
    #     self._node_info['uid'] = uids.cumsum() - uids

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Should be an hdf5 file with a few key attributes.
        """
        fn = args[0]

        if not h5py.is_hdf5(fn):
            return False

        groups = ["config", "simulation"]

        with h5py.File(fn, mode='r') as f:
            for group in groups:
                if group not in f:
                    return False
                if not isinstance(f[group], h5py.Group):
                    return False
        return True
