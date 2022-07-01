"""
ConsistentTreesHDF5Arbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from collections import defaultdict
import h5py
import numpy as np

from yt.funcs import \
    get_pbar

from ytree.data_structures.io import \
    DataFile, \
    DefaultRootFieldIO, \
    TreeFieldIO

class ChunkStore:
    def __init__(self, chunk_size=262144):
        self.chunk_size = chunk_size
        self.reset()

    def reset(self):
        self.data = {}
        self.ind = {}

    def get(self, fh, field, index):
        start, end = index
        si, ei = self.ind.get(field, (0, 0))

        if field not in self.data or ei < end or si > start:
            si = start
            ei = start + self.chunk_size
            self.ind[field] = (si, ei)
            self.data[field] = fh[field][si:ei]

        data_s = start - si
        data_e = end - si
        return self.data[field][data_s:data_e]

class ConsistentTreesHDF5DataFile(DataFile):
    def __init__(self, filename, linkname):
        super().__init__(filename)
        self.linkname = linkname
        self.real_fh = None
        self._field_cache = ChunkStore()

    def open(self):
        self.real_fh = h5py.File(self.filename, mode="r")
        if self.linkname is None:
            self.fh = self.real_fh
        else:
            self.fh = self.real_fh[self.linkname]

    def close(self):
        self.real_fh.close()
        self.fh = None

class ConsistentTreesHDF5TreeFieldIO(TreeFieldIO):
    def _read_fields(self, root_node, fields, dtypes=None,
                     root_only=False):
        """
        Read fields from disk for a single tree.
        """

        data_file = self.arbor.data_files[root_node._fi]

        close = False
        if data_file.fh is None:
            close = True
            data_file.open()
        fh = data_file.fh['Forests']
        if self.arbor._aos:
            fh = fh['halos']

        if root_only:
            index = (root_node._si, root_node._si+1)
        else:
            index = (root_node._si, root_node._ei)

        field_cache = data_file._field_cache
        field_data = dict((field, field_cache.get(fh, field, index))
                          for field in fields)

        if close:
            data_file.close()
            for field in fields:
                field_data[field] = field_data[field].copy()

        self._apply_units(fields, field_data)

        return field_data

class ConsistentTreesHDF5RootFieldIO(DefaultRootFieldIO):
    """
    Read in fields for first node in all trees/forest.

    This function is optimized for the struct of arrays layout.
    It will work for array of structs layout, but field access
    will be 1 to 2 orders of magnitude slower.
    """
    def _read_fields(self, storage_object, fields, dtypes=None):
        if dtypes is None:
            dtypes = {}

        arbor = self.arbor
        arbor._plant_trees()

        # Use the _node_io_loop machinery to get the data files
        # and corresponding tree indices.
        data_files, index_list, _ = arbor._node_io_loop_prepare(None)

        c = 0
        rdata = defaultdict(list)

        iend = arbor._file_count.cumsum()
        istart = iend - arbor._file_count

        pbar = get_pbar('Reading root fields', arbor.size)
        for idf, (data_file, nodes) in enumerate(zip(data_files, index_list)):
            my_indices = arbor._node_info['_si'][istart[idf]:iend[idf]]
            arbor._node_io_loop_start(data_file)

            fh = data_file.fh['Forests']
            if self.arbor._aos:
                fh = fh['halos']

            for field in fields:
                darray = fh[field][()]
                rdata[field].append(darray[my_indices])

            arbor._node_io_loop_finish(data_file)

            c += my_indices.size
            pbar.update(c)
        pbar.finish()

        field_data = {}
        for field in fields:
            data = np.concatenate(rdata[field])
            dtype = dtypes.get(field)
            if dtype is not None:
                data = data.astype(dtype)
            field_data[field] = data

        self._apply_units(fields, field_data)

        return field_data
