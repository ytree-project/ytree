"""
Gadget4Arbor io classes and member functions



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

from ytree.data_structures.io import \
    DataFile, \
    TreeFieldIO

class Gadget4DataFile(DataFile):
    def _load_properties(self):
        self.open()
        self._size = int(self.fh["Header"].attrs["Ntrees_ThisFile"])
        self._file_count = self.fh["TreeTable/Length"][()]
        self._file_offsets = self.fh["TreeTable/StartOffset"][()]
        self.close()

    _size = None
    @property
    def size(self):
        if self._size is not None:
            return self._size
        self._load_properties()
        return self._size

    _file_offsets = None
    @property
    def file_offsets(self):
        if self._file_offsets is not None:
            return self._file_offsets
        self._load_properties()
        return self._file_offsets

    _file_count = None
    @property
    def file_count(self):
        if self._file_count is not None:
            return self._file_count
        self._load_properties()
        return self._file_count

    def open(self):
        self.fh = h5py.File(self.filename, mode="r")

    def close(self):
        self.fh.close()
        self.fh = None

class Gadget4TreeFieldIO(TreeFieldIO):
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
        g = fh["TreeHalos"]

        _si = root_node._si
        if root_only:
            index = slice(_si, _si + 1)
        else:
            index = slice(_si, _si + root_node._tree_size)

        field_cache = {}
        field_data = {}
        freg = re.compile(r"(^.+)_(\d+$)")
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

        self._apply_units(rfields, field_data)

        return field_data

    def _get_arbor_fields(self, root_node, field_data,
                          fields, afields, root_only):
        """
        Generate special fields from the arbor/treenode.
        """

        adata = {}

        if "uid" in afields:
            if root_only:
                adata["uid"] = np.array([root_node.uid])
            else:
                adata["uid"] = root_node.uid + \
                  np.arange(root_node._tree_size)

        if "desc_uid" in afields:
            if "TreeDescendant" in fields:
                desc_uids = field_data["TreeDescendant"].copy()
            else:
                desc_uids = field_data.pop("TreeDescendant")
            desc_uids[desc_uids != -1] += root_node.uid
            adata["desc_uid"] = desc_uids

        return adata
