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
import re

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

        fi = self.arbor.field_info
        afields = [field for field in fields
                   if fi[field].get("source") == "arbor"]
        rfields = list(set(fields).difference(afields))

        for afield in afields:
            rfields.extend(
                [dfield for dfield in fi[afield].get("dependencies", [])
                 if dfield not in rfields])

        data_file = self.arbor.data_files[root_node._fi]
        close = False
        if data_file.fh is None:
            close = True
            data_file.open()
        fh = data_file.fh
        g = fh[f"Tree{root_node._si}"]

        if root_only:
            index = slice(0, 1)
        else:
            index = ()

        field_cache = {}
        field_data = {}
        freg = re.compile("(^.+)_(\d+$)")
        for field in rfields:
            fs = freg.search(field)
            if fs and fs.groups()[0] in g:
                fieldname, ifield = fs.groups()
                ifield = int(ifield)
                if fieldname not in field_cache:
                    field_cache[fieldname] = g[fieldname][index]
                field_data[field] = field_cache[fieldname][:, ifield]
            else:
                field_data[field] = g[field][index]

        if afields:
            field_data.update(self._get_arbor_fields(
                root_node, field_data, fields, afields, root_only))

        if close:
            data_file.close()

        for field in rfields:
            units = fi[field].get("units", "")
            if units != "":
                field_data[field] = \
                  self.arbor.arr(field_data[field], units)

        return field_data

    def _get_arbor_fields(self, root_node, field_data,
                          fields, afields, root_only):
        """
        Generate special fields from the arbor/treenode.
        """

        adata = {}

        if "uid" in afields:
            if root_only:
                adata["uid"] = np.array([root_node._tree_size])
            else:
                adata["uid"] = np.arange(root_node._tree_size)

        if "desc_uid" in afields:
            if "Descendant" in fields:
                desc_uids = field_data["Descendant"].copy()
            else:
                desc_uids = field_data.pop("Descendant")
            desc_uids[1:] += root_node.uid
            adata["desc_uid"] = desc_uids

        return adata

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
