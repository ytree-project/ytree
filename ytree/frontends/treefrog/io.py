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
        """
        Calculate snapshots and snapshot-offsets where each forest appears last.

        For N forests and M snapshots, the data files contain two MxN arrays of:
        - the size of forest i in each snapshot j
        - the offset of forest i in each snapshot j

        In this function, we calculate two things for each forest:
        - the last (i.e. latest in time) snapshot in which the forest exists
        - the file offset within that last snapshot

        Since ytree reads from the root backward, this tell us where to start
        reading for any given forest.
        """
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

    def read_data(self, group, field, frange=None):
        if frange is None:
            frange = ()
        # This is the easiest way I can think of to fix the
        # descendent ids of roots.
        if field == "Descendant":
            data = self.fh[group][field][()][frange]
            ids = self.fh[group]["ID"][()][frange]
            data[data == ids] = -1
            return data
        return self.fh[group][field][()][frange]

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
        my_dtypes = self._determine_dtypes(
            fields, override_dict=dtypes)

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
                rdata[field].append(
                    data_file.read_data(
                        group, field,
                        frange=slice(offset,offset+size)))

            for field in afields:
                rdata[field].append(self._get_arbor_field(field, gi, size))

        for field, data in rdata.items():
            rdata[field] = np.concatenate(data)

        if close:
            data_file.close()

        field_data = root_node.field_data
        for field in fields:
            field_data[field] = rdata[field]
            dtype = my_dtypes.get(field, fi[field].get("dtype", None))
            if dtype is not None:
                field_data[field] = field_data[field].astype(dtype)

        self._apply_units(fields, field_data)

        return field_data

    def _get_arbor_field(self, field, gi, size):
        if field == "scale_factor":
            return self.arbor._scale_factors[gi] * np.ones(size)
        else:
            raise ArborFieldNotFound(field, arbor=self.arbor)

class TreeFrogRootFieldIO(DefaultRootFieldIO):
    """
    Read fields for the roots of all forests.

    Each data file stores the latest snapshot where a forest exists
    and the offset within that snapshot. We use this information to
    open only the HDF5 groups that have data we need.
    """
    def _read_fields(self, storage_object, fields, dtypes=None):
        if dtypes is None:
            dtypes = {}
        my_dtypes = self._determine_dtypes(
            fields, override_dict=dtypes)

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

            size = nodes.size
            # the index of the last snapshot for each forest
            s1 = data_file.arbor_start[nodes]
            # the offset within that snapshot
            o1 = data_file.arbor_offset[nodes]

            fdata = {}
            # np.unique(s1) gives us the total number of HDF5 groups we need to open
            for gi in np.unique(s1):
                group = f"Snap_{gi:03d}"
                # which forests' roots are in this group
                isnap = np.where(s1 == gi)[0]

                for field in rfields:
                    gdata = data_file.read_data(group, field)
                    if field not in fdata:
                        fdata[field] = np.empty(size, dtype=gdata.dtype)
                    # o1[isnap] is the list of file offsets for this HDF5 group
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
        for field in fields:
            data = np.concatenate(rdata[field])
            dtype = my_dtypes.get(field)
            if dtype is not None:
                data = data.astype(dtype)
            field_data[field] = data

        self._apply_units(fields, field_data)

        return field_data

    def _get_arbor_field(self, field, s1):
        if field == "scale_factor":
            return self.arbor._scale_factors[s1]
        else:
            raise ArborFieldNotFound(field, arbor=self.arbor)
