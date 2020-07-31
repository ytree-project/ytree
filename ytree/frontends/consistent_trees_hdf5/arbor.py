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
import re

from yt.funcs import \
    get_pbar

from ytree.data_structures.arbor import \
    Arbor
from ytree.data_structures.tree_node import \
    TreeNode

from ytree.frontends.consistent_trees.arbor import \
    ConsistentTreesGroupArbor
from ytree.frontends.consistent_trees.utilities import \
    parse_ctrees_header
from ytree.frontends.consistent_trees_hdf5.fields import \
    ConsistentTreesHDF5FieldInfo
from ytree.frontends.consistent_trees_hdf5.io import \
    ConsistentTreesHDF5DataFile, \
    ConsistentTreesHDF5RootFieldIO, \
    ConsistentTreesHDF5TreeFieldIO
from ytree.utilities.exceptions import \
    ArborDataFileEmpty

_access_names = {
    'tree':   {'group'     : 'TreeInfo',
               'unique_id' : 'TreeRootID',
               'offset'    : 'TreeHalosOffset',
               'size'      : 'TreeNhalos',
               'total'     : 'TotNtrees',
               'file_size' : 'Ntrees'},
    'forest': {'group'     : 'ForestInfo',
               'unique_id' : 'ForestID',
               'offset'    : 'ForestHalosOffset',
               'size'      : 'ForestNhalos',
               'total'     : 'TotNforests',
               'file_size' : 'Nforests'}
}

class ConsistentTreesHDF5Arbor(Arbor):
    """
    Arbors loaded from consistent-trees tree_*.dat files.
    """

    _parameter_file_is_data_file = True
    _field_info_class = ConsistentTreesHDF5FieldInfo
    _root_field_io_class = ConsistentTreesHDF5RootFieldIO
    _tree_field_io_class = ConsistentTreesHDF5TreeFieldIO
    _default_dtype = np.float32
    _node_io_attrs = ('_fi', '_si', '_ei')

    def __init__(self, filename, access='tree'):
        if access not in _access_names:
            raise ValueError(
                ('Invalid access value: %s. '
                 'Valid options are: %s.') % (access, _access_names))
        self.access = access
        super(ConsistentTreesHDF5Arbor, self).__init__(filename)

    _node_io_loop_prepare = ConsistentTreesGroupArbor._node_io_loop_prepare

    def _node_io_loop_start(self, data_file):
        data_file._field_cache = {}
        data_file.open()

    def _node_io_loop_finish(self, data_file):
        data_file._field_cache = {}
        data_file.close()

    def _get_data_files(self):
        aname = _access_names[self.access]['file_size']
        with h5py.File(self.filename, mode='r') as f:
            self.data_files = \
              [ConsistentTreesHDF5DataFile(self.filename, lname)
               for lname in f]
            self._file_count = \
              np.array([f[lname].attrs[aname] for lname in f])

    def _parse_parameter_file(self):
        f = h5py.File(self.filename, mode='r')
        fgroup = f.get('File0')
        if fgroup is None:
            raise ArborDataFileEmpty(self.filename)
        my_fi = dict((field, {'dtype': data.dtype})
                    for field, data in fgroup['Forests'].items())
        aname = _access_names[self.access]['total']
        self._size = f.attrs[aname]
        header = fgroup.attrs['Consistent Trees_metadata'].astype(str)
        header = header.tolist()
        f.close()

        header_fi = parse_ctrees_header(
            self, header, ntrees_in_file=False)
        # Do some string manipulation to match the header with
        # altered names in the hdf5 file.
        new_fi = {}
        for field in header_fi:
            new_field = field
            # remove ?| characters
            new_field = re.sub(r'[?|]', '', new_field)
            # replace []/() characters with _
            new_field = re.sub(r'[\[\]\/\(\)]', '_', new_field)
            # remove leading/trailing underscores
            new_field = new_field.strip('_')
            # replace double underscore with single underscore
            new_field = new_field.replace('__', '_')

            new_fi[new_field] = header_fi[field].copy()
            if 'column' in new_fi[new_field]:
                del new_fi[new_field]['column']

        for field in my_fi:
            my_fi[field].update(new_fi.get(field, {}))

        self.field_list = list(my_fi.keys())
        self.field_info.update(my_fi)

    def _plant_trees(self):
        if self.is_planted or self._size == 0:
            return

        my_access = _access_names[self.access]
        groupname  = my_access['group']
        uidname    = my_access['unique_id']
        offsetname = my_access['offset']
        sizename   = my_access['size']

        c = 0
        file_offsets = self._file_count.cumsum() - self._file_count
        pbar = get_pbar('Planting %ss' % self.access, self._size)
        for idf, data_file in enumerate(self.data_files):
            data_file.open()
            uids = data_file.fh[groupname][uidname][()]
            offsets = data_file.fh[groupname][offsetname][()]
            tree_sizes = data_file.fh[groupname][sizename][()]
            data_file.close()

            istart = file_offsets[idf]
            iend = istart + uids.size
            self._node_info['uid'][istart:iend] = uids
            self._node_info['_fi'][istart:iend] = idf
            self._node_info['_si'][istart:iend] = offsets
            self._node_info['_ei'][istart:iend] = offsets + tree_sizes
            c += uids.size
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
        with h5py.File(fn, mode='r') as f:
            for attr in ['Nfiles', 'TotNforests', 'TotNhalos', 'TotNtrees']:
                if attr not in f.attrs:
                    return False
        return True
