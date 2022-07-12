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

from unyt import uconcatenate

from ytree.data_structures.io import \
    DataFile, \
    TreeFieldIO

class Gadget4DataFile(DataFile):
    _io_attrs = ("ntrees", "nnodes", "tree_sizes", "offsets")
    def _load_properties(self):
        self.open()
        self.ntrees = int(self.fh["Header"].attrs["Ntrees_ThisFile"])
        self.nnodes = int(self.fh["Header"].attrs["Nhalos_ThisFile"])
        if self.ntrees > 0:
            self.tree_sizes = self.fh["TreeTable/Length"][()]
            self.offsets = self.fh["TreeTable/StartOffset"][()]
        else:
            self.tree_sizes = None
            self.offsets = None
        self.close()

    def __getattr__(self, attr):
        if attr in self._io_attrs:
            self._load_properties()
            return getattr(self, attr)
        raise AttributeError(attr)

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

        if root_only:
            fei = root_node._fi
        else:
            fei = root_node._fei

        freg = re.compile(r"(^.+)_(\d+$)")
        field_data = {field: [] for field in rfields}
        for dfi in range(root_node._fi, fei+1):
            data_file = self.arbor.data_files[dfi]
            close = False
            if data_file.fh is None:
                close = True
                data_file.open()
            fh = data_file.fh
            g = fh["TreeHalos"]

            si = root_node._si
            if root_only:
                my_slice = slice(si, si+1)
            else:
                if dfi == root_node._fi:
                    my_start = si
                else:
                    my_start = None

                if dfi == fei:
                    my_end = root_node._ei
                else:
                    my_end = None

                my_slice = slice(my_start, my_end)

            field_cache = {}
            for field in rfields:
                fs = freg.search(field)
                if fs and fs.groups()[0] in g:
                    fieldname, ifield = fs.groups()
                    ifield = int(ifield)
                    if fieldname not in field_cache:
                        field_cache[fieldname] = g[fieldname][my_slice]
                    field_data[field].append(field_cache[fieldname][:, ifield])
                else:
                    field_data[field].append(g[field][my_slice])

            if close:
                data_file.close()

        for field in field_data:
            field_data[field] = uconcatenate(field_data[field])

        if afields:
            field_data.update(self._get_arbor_fields(
                root_node, field_data, fields, afields, root_only))

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
