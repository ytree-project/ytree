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

import h5py
import numpy as np

from yt.funcs import \
    get_pbar

from ytree.data_structures.arbor import \
    Arbor

from ytree.frontends.moria.fields import \
    MoriaFieldInfo
from ytree.frontends.moria.io import \
    MoriaDataFile, \
    MoriaRootFieldIO, \
    MoriaTreeFieldIO
from ytree.utilities.logger import \
    ytreeLogger as mylog

class MoriaArbor(Arbor):
    """
    Arbors from Moria merger trees.
    """

    _suffix = ".hdf5"
    _data_file_class = MoriaDataFile
    _field_info_class = MoriaFieldInfo
    _root_field_io_class = MoriaRootFieldIO
    _tree_field_io_class = MoriaTreeFieldIO
    _node_io_attrs = ('_ai', '_si', '_ei')

    def _parse_parameter_file(self):
        f = h5py.File(self.parameter_filename, mode='r')
        g = f["simulation"]
        self.hubble_constant = float(g.attrs['cosmo_h'])
        self.omega_matter = g.attrs['cosmo_Omega_m']
        self.omega_lambda = g.attrs['cosmo_Omega_L']
        self.omega_radiation = g.attrs['cosmo_Omega_r']
        self.box_size = self.quan(g.attrs['box_size'], 'Mpc/h')
        self._redshifts = self.arr(g.attrs['snap_z'], '')
        self._scale_factors = self.arr(g.attrs['snap_a'], '')
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

        field_list.append("snap_index")
        fi["snap_index"] = {"source": "arbor", "dtype": int}

        self.field_list = field_list
        self.field_info.update(fi)

    def _get_data_files(self):
        self.data_files = [self._data_file_class(self.parameter_filename)]

    def _plant_trees(self):
        if self.is_planted:
            return

        f = h5py.File(self.parameter_filename, mode='r')
        status = f["status_sparta"][()]
        root_status = status[-1]
        hosts = root_status == 10
        self._size = hosts.sum()
        self._node_info['_ai'][:] = np.arange(self._size)
        self._node_info['_si'][:] = np.where(hosts)[0]
        self._node_info['_ei'][:-1] = self._node_info['_si'][1:]
        self._node_info['_ei'][-1] = root_status.size
        self._node_info['uid'][:] = f["id"][-1][hosts]
        f.close()

        pbar = get_pbar('Planting trees', self._size)
        si = self._node_info['_si']
        ei = self._node_info['_ei']
        for i in range(self._size):
            tree_status = status[:, si[i]:ei[i]]
            self._node_info['_tree_size'][i] = (tree_status != 0).sum()
            pbar.update(i+1)
        pbar.finish()

    def _setup_tree(self, tree_node, **kwargs):
        """
        Check for desc_uids missing from uid list.
        """

        super()._setup_tree(tree_node, **kwargs)
        uids = tree_node.uids
        desc_uids = tree_node.desc_uids
        missing = np.setdiff1d(desc_uids, uids)
        missing = np.setdiff1d(missing, [-1])
        if missing.size == 0:
            return

        mfields = ["snap_index", "descendant_index"]
        field_data  = self._node_io._read_fields(tree_node, mfields)

        xsize = self._redshifts.size - 1
        ysize = tree_node._ei - tree_node._si
        xindex = xsize - field_data["snap_index"] - 1
        yindex = field_data["descendant_index"] - tree_node._si

        for muid in missing:
            mi = np.where(desc_uids == muid)[0]
            ndi = np.ravel_multi_index([xindex[mi], yindex[mi]], (xsize, ysize))
            for my_mi, my_ndi in zip(mi, ndi):
                new_uid = uids[np.where(my_ndi == tree_node._status)][0]
                mylog.info(f"Reassigning descendent of halo {uids[my_mi]} from "
                           f"{desc_uids[my_mi]} to {new_uid}.")
                desc_uids[my_mi] = new_uid

    def _node_io_loop_prepare(self, nodes):
        self._plant_trees()

        if nodes is None:
            my_size = self.size
        else:
            my_size = nodes.size
        indices = np.arange(my_size)

        return self.data_files, [indices], None

    def _node_io_loop_start(self, data_file):
        data_file.full_read = True

    def _node_io_loop_finish(self, data_file):
        data_file.full_read = False
        data_file.field_cache = None

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
