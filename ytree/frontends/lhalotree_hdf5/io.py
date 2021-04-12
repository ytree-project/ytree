"""
LHaloTreeHDF5Arbor io classes and member functions



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

class LHaloTreeHDF5DataFile(DataFile):
    def __init__(self, filename, linkname):
        super(LHaloTreeHDF5DataFile, self).__init__(filename)

        self.open()
        self._size = self.fh["Header"].attrs["NtreesPerFile"]
        self.close()

    def open(self):
        self.fh = h5py.File(self.filename, mode="r")

    def close(self):
        self.fh.close()
        self.fh = None

class LHaloTreeHDF5TreeFieldIO(TreeFieldIO):
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

        fi = self.arbor.field_info
        for field in fields:
            units = fi[field].get("units", "")
            if close:
                field_data[field] = field_data[field].copy()
            if units != "":
                field_data[field] = \
                  self.arbor.arr(field_data[field], units)

        return field_data

class LHaloTreeHDF5RootFieldIO(DefaultRootFieldIO):
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
        fi = self.arbor.field_info
        for field in fields:
            data = np.concatenate(rdata[field])
            dtype = dtypes.get(field)
            if dtype is not None:
                data = data.astype(dtype)
            units = fi[field].get("units", "")
            if units != "":
                data = self.arbor.arr(data, units)
            field_data[field] = data

        return field_data
