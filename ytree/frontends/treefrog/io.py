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
from ytree.utilities.exceptions import \
    ArborFieldNotFound

class TreeFrogDataFile(DataFile):
    def _calculate_arbor_offsets(self):
        close = self.fh is None
        self.open()
        fh = self.fh

        offsets = fh["ForestInfoInFile/ForestOffsetsAllSnaps"][()]
        sizes = fh["ForestInfoInFile/ForestSizesAllSnaps"][()]
        size = sizes.shape[0]
        s1 = np.empty(size, dtype=int)
        o1 = np.empty(size, dtype=int)
        for i in range(size):
            s1[i] = np.where(sizes[i] > 0)[0][-1]
            o1[i] = offsets[i, s1[i]]

        if close:
            self.close()

        self._arbor_start = s1
        self._arbor_offset = o1

    _arbor_start = None
    @property
    def arbor_start(self):
        if self._arbor_start is None:
            self._calculate_arbor_offsets()
        return self._arbor_start

    _arbor_offset = None
    @property
    def arbor_offset(self):
        if self._arbor_offset is None:
            self._calculate_arbor_offsets()
        return self._arbor_offset

    def open(self):
        if self.fh is None:
            self.fh = h5py.File(self.filename, mode="r")

class TreeFrogTreeFieldIO(TreeFieldIO):
    def _read_fields(self, root_node, fields, dtypes=None,
                     root_only=False):
        """
        Read fields from disk for a single tree.
        """

        if dtypes is None:
            dtypes = {}

        fi = self.arbor.field_info
        afields = [field for field in fields
                   if fi[field].get("source") == "arbor"]
        rfields = list(set(fields).difference(afields))

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
            for field in rfields:
                rdata[field].append(fh[group][field][offset:offset+size])

            for field in afields:
                rdata[field].append(self._get_arbor_field(field, gi, size))

        for field, data in rdata.items():
            rdata[field] = np.concatenate(data)

        if close:
            data_file.close()

        field_data = root_node._field_data
        for field in fields:
            field_data[field] = rdata[field]
            dtype = dtypes.get(field, fi[field].get("dtype", None))
            if dtype is not None:
                field_data[field] = field_data[field].astype(dtype)
            units = fi[field].get("units", "")
            if units != "":
                field_data[field] = self.arbor.arr(field_data[field], units)

        return field_data

    def _get_arbor_field(self, field, gi, size):
        if field == "scale_factor":
            return self.arbor._scale_factors[gi] * np.ones(size)
        else:
            raise ArborFieldNotFound(field, arbor=self.arbor)

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

        fi = self.arbor.field_info
        afields = [field for field in fields
                   if fi[field].get("source") == "arbor"]
        rfields = list(set(fields).difference(afields))

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
            size = nodes.size
            s1 = data_file.arbor_start[nodes]
            o1 = data_file.arbor_offset[nodes]

            fdata = {}
            for gi in np.unique(s1):
                group = f"Snap_{gi:03d}"
                isnap = np.where(s1 == gi)[0]

                for field in rfields:
                    gdata = fh[group][field][()]
                    if field not in fdata:
                        fdata[field] = np.empty(size, dtype=gdata.dtype)
                    fdata[field][isnap] = gdata[o1[isnap]]

            for field in rfields:
                rdata[field].append(fdata[field])

            for field in afields:
                rdata[field].append(self._get_arbor_field(field, s1))

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

    def _get_arbor_field(self, field, s1):
        if field == "scale_factor":
            return self.arbor._scale_factors[s1]
        else:
            raise ArborFieldNotFound(field, arbor=self.arbor)
