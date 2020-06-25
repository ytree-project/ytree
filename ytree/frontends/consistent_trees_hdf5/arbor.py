"""
ConsistentTreesHDF5Arbor class and member functions



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
from ytree.data_structures.tree_node import \
    TreeNode

from ytree.frontends.consistent_trees_hdf5.fields import \
    ConsistentTreesHDF5FieldInfo
from ytree.frontends.consistent_trees_hdf5.io import \
    ConsistentTreesHDF5DataFile, \
    ConsistentTreesHDF5TreeFieldIO

class ConsistentTreesHDF5Arbor(Arbor):
    """
    Arbors loaded from consistent-trees tree_*.dat files.
    """

    _parameter_file_is_data_file = True
    _field_info_class = ConsistentTreesHDF5FieldInfo
    _tree_field_io_class = ConsistentTreesHDF5TreeFieldIO
    _default_dtype = np.float32

    def _node_io_loop_prepare(self, root_nodes):
        return self.data_files, [root_nodes]

    def _node_io_loop_start(self, data_file):
        data_file.open()

    def _node_io_loop_finish(self, data_file):
        data_file.close()

    def _get_data_files(self):
        with h5py.File(self.filename, mode='r') as f:
            self.data_files = \
              [ConsistentTreesHDF5DataFile(self.filename, lname)
               for lname in f]
            self._file_count = \
              np.array([f[lname].attrs['Ntrees'] for lname in f])

    def _parse_parameter_file(self):
        ### TODO: can these attributes be saved?
        self.omega_matter = 0.3
        self.omega_lambda = 0.7
        self.hubble_constant = 0.7
        self.box_size = self.quan(100, 'Mpc/h')

        f = h5py.File(self.filename, mode='r')
        fgroup = f['File0'] # or this: f[files[0]]['Forests']
        fi = dict((field, {'dtype': data.dtype})
                  for field, data in fgroup['Forests'].items())
        self._ntrees = f.attrs['TotNtrees']
        f.close()

        self.field_list = list(fi.keys())
        self.field_info.update(fi)

    def _plant_trees(self):
        self._trees = np.empty(self._ntrees, dtype=np.object)
        if self._ntrees == 0:
            return

        file_offsets = self._file_count.cumsum() - self._file_count
        pbar = get_pbar('Planting trees', self._ntrees)
        for idf, data_file in enumerate(self.data_files):
            data_file.open()
            uids = data_file.fh['TreeInfo']['TreeRootID'][()]
            offsets = data_file.fh['TreeInfo']['TreeHalosOffset'][()]
            tree_sizes = data_file.fh['TreeInfo']['TreeNhalos'][()]
            data_file.close()

            ifile = file_offsets[idf]
            for ih in range(uids.size):
                my_node = TreeNode(uids[ih], arbor=self, root=True)
                my_node._fi = idf
                my_node._si = offsets[ih]
                my_node._ei = my_node._si + tree_sizes[ih]
                self._trees[ih+ifile] = my_node
                pbar.update(1)
        pbar.finish()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Should be an hdf5 file with a few key attributes.
        """
        fn = args[0]
        if not h5py.is_hdf5(fn):
            return False
        with h5py.File(fn, mode='r') as f:
            for attr in ['Nfiles', 'TotNhalos', 'TotNtrees']:
                if attr not in f.attrs:
                    return False
        return True
