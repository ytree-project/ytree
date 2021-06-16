"""
TreeFrogArbor io classes and member functions



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

class TreeFrogDataFile(DataFile):
    # def __init__(self, filename, linkname):
    #     super(TreeFrogDataFile, self).__init__(filename)
    #     self.linkname = linkname
    #     self.real_fh = None
    #     self._field_cache = ChunkStore()

    def open(self):
        self.fh = h5py.File(self.filename, mode="r")

    def close(self):
        self.fh.close()
        self.fh = None

class TreeFrogTreeFieldIO(TreeFieldIO):
    def _read_fields(self, root_node, fields, dtypes=None,
                     root_only=False):
        """
        Read fields from disk for a single tree.
        """

        if dtypes is None:
            dtypes = {}

        data_file = self.arbor.data_files[root_node._fi]

        close = False
        if data_file.fh is None:
            close = True
            data_file.open()

        fh = data_file.fh
        si = root_node._si

        if not hasattr(root_node, "_offsets"):
            root_node._offsets = fh["ForestInfoInFile/ForestOffsetsAllSnaps"][si]
        offsets = root_node._offsets
        if not hasattr(root_node, "_sizes"):
            root_node._sizes = fh["ForestInfoInFile/ForestSizesAllSnaps"][si]
        sizes = root_node._sizes

        in_snap = np.where(sizes > 0)[0]
        gs = in_snap[-1]
        if root_only:
            ge = gs
        else:
            ge = in_snap[0]

        rdata = defaultdict(list)
        for gi in range(gs, ge-1, -1):
            group = f"Snap_{gi:03d}"
            offset = offsets[gi]
            size = sizes[gi]
            for field in fields:
                rdata[field].append(fh[group][field][offset:offset+size])

        for field, data in rdata.items():
            rdata[field] = np.concatenate(data)

        if close:
            data_file.close()

        field_data = root_node._field_data
        fi = self.arbor.field_info
        for field in fields:
            field_data[field] = rdata[field]
            dtype = dtypes.get(field, fi[field].get("dtype", None))
            if dtype is not None:
                field_data[field] = field_data[field].astype(dtype)
            units = fi[field].get("units", "")
            if units != "":
                field_data[field] = self.arbor.arr(field_data[field], units)

        return field_data

class TreeFrogRootFieldIO(DefaultRootFieldIO):
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
        pbar = get_pbar('Reading root fields', arbor.size)
        for idf, (data_file, nodes) in enumerate(zip(data_files, index_list)):
            arbor._node_io_loop_start(data_file)

            fh = data_file.fh
            offsets = fh["ForestInfoInFile/ForestOffsetsAllSnaps"][()][nodes]
            sizes = fh["ForestInfoInFile/ForestSizesAllSnaps"][()][nodes]
            size = nodes.size
            s1 = np.empty(size, dtype=int)
            o1 = np.empty(size, dtype=int)
            for i in range(size):
                s1[i] = np.where(sizes[i] > 0)[0][-1]
                o1[i] = offsets[i, s1[i]]

            fdata = {}
            for gi in np.unique(s1):
                group = f"Snap_{gi:03d}"
                for field in fields:
                    gdata = fh[group][field][()]
                    if field not in fdata:
                        fdata[field] = np.empty(size, dtype=gdata.dtype)
                    isnap = np.where(s1 == gi)[0]
                    fdata[field][isnap] = gdata[o1[isnap]]

            for field in fields:
                rdata[field].append(fdata[field])

            arbor._node_io_loop_finish(data_file)

            c += size
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
