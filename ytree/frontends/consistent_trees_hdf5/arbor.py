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
    SegmentedArbor
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
from ytree.utilities.logger import \
    ytreeLogger as mylog

_access_names = {
    'tree':   {'group'     : 'TreeInfo',
               'host_id'   : 'TreeRootID',
               'offset'    : 'TreeHalosOffset',
               'size'      : 'TreeNhalos',
               'total'     : 'TotNtrees',
               'file_size' : 'Ntrees',
               'host_attr' : 'tree_root_id'},
    'forest': {'group'     : 'ForestInfo',
               'host_id'   : 'ForestID',
               'offset'    : 'ForestHalosOffset',
               'size'      : 'ForestNhalos',
               'total'     : 'TotNforests',
               'file_size' : 'Nforests',
               'host_attr' : 'forest_id'}
}

class ConsistentTreesHDF5Arbor(SegmentedArbor):
    """
    Arbors loaded from consistent-trees data converted into HDF5.
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
                f"Invalid access value: {access}. Valid options are: {_access_names}.")
        self.access = access
        self._node_io_attrs += (_access_names[access]['host_attr'],)
        super().__init__(filename)

    def _node_io_loop_finish(self, data_file):
        data_file._field_cache.reset()
        data_file.close()

    @property
    def _virtual_dataset(self):
        return re.search(r"\_\d+\.h5$", self.parameter_filename) is None

    def _get_data_files(self):
        aname = _access_names[self.access]['file_size']

        if self._virtual_dataset:
            with h5py.File(self.filename, mode='r') as f:
                self.data_files = \
                  [ConsistentTreesHDF5DataFile(self.filename, lname) for lname in f]
                self._file_count = \
                  np.array([f[lname].attrs[aname] for lname in f])
        else:
            if not isinstance(self.filename, list):
                fns = [self.filename]
            else:
                fns = self.filename
            self.data_files = [ConsistentTreesHDF5DataFile(fn, None) for fn in fns]
            self._file_count = \
              np.array([h5py.File(fn, mode='r').attrs[aname] for fn in fns])
            self._size = sum(self._file_count)

    def _parse_parameter_file(self):
        f = h5py.File(self.parameter_filename, mode='r')

        # Is the file a collection of virtual data sets
        # pointing to multiple data files?
        virtual = self._virtual_dataset
        if virtual:
            fgroup = f.get('File0')
            if fgroup is None:
                raise ArborDataFileEmpty(self.filename)
        else:
            fgroup = f

        if 'halos' in fgroup['Forests']:
            # array of structs layout
            mylog.warning(
                "This dataset was written in array of structs format. "
                "Field access will be significantly slower than struct "
                "of arrays format.")
            self._aos = True
            ftypes = fgroup['Forests/halos'].dtype
            my_fi = dict((ftypes.names[i], {'dtype': ftypes[i]})
                         for i in range(len(ftypes)))
        else:
            # struct of arrays layout
            self._aos = False
            my_fi = dict((field, {'dtype': data.dtype})
                        for field, data in fgroup['Forests'].items())

        if virtual:
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

        my_access  = _access_names[self.access]
        groupname  = my_access['group']
        hostname   = my_access['host_id']
        hostattr   = my_access['host_attr']
        offsetname = my_access['offset']
        sizename   = my_access['size']

        c = 0
        file_offsets = self._file_count.cumsum() - self._file_count
        pbar = get_pbar(f'Planting {self.access}s', self._size)
        for idf, data_file in enumerate(self.data_files):
            data_file.open()
            hostids = data_file.fh[groupname][hostname][()]
            offsets = data_file.fh[groupname][offsetname][()]
            tree_sizes = data_file.fh[groupname][sizename][()]
            data_file.close()

            istart = file_offsets[idf]
            iend = istart + offsets.size
            self._node_info[hostattr][istart:iend] = hostids
            self._node_info['_fi'][istart:iend] = idf
            self._node_info['_si'][istart:iend] = offsets
            self._node_info['_ei'][istart:iend] = offsets + tree_sizes
            self._node_info['_tree_size'][istart:iend] = tree_sizes
            c += offsets.size
            pbar.update(c)
        pbar.finish()
        self._node_info['uid'] = self['uid']

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Should be an hdf5 file with a few key attributes.
        """
        fns = args[0]
        if not isinstance(fns, list):
            fns = [fns]

        for fn in fns:
            if not h5py.is_hdf5(fn):
                return False
            # single data file
            if re.search(r"\_\d+\.h5$", fn):
                attrs = ['Nforests', 'Ntrees', 'Nhalos']
            # virtual data set file
            else:
                if len(fns) > 1:
                    raise RuntimeError(
                        'Virtual data set file cannot be given in a list.')
                attrs = ['Nfiles', 'TotNforests', 'TotNhalos', 'TotNtrees']

            with h5py.File(fn, mode='r') as f:
                for attr in attrs:
                    if attr not in f.attrs:
                        return False
        return True
