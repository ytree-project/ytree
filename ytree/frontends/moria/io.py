"""
MoriaArbor io classes and member functions



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
    DefaultRootFieldIO, \
    DataFile, \
    TreeFieldIO

class MoriaDataFile(DataFile):
    def open(self):
        self.fh = h5py.File(self.filename, mode="r")

    def close(self):
        self.fh.close()
        self.fh = None

class MoriaTreeFieldIO(TreeFieldIO):
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

        data_file = self.arbor.data_files[0]
        close = False
        if data_file.fh is None:
            close = True
            data_file.open()
        fh = data_file.fh

        if root_only:
            index = (-1, slice(root_node._si, root_node._si+1))
            dfilter = None
        else:
            index = (slice(None), slice(root_node._si, root_node._ei))
            status = fh["status_sparta"][index]
            status = self._transform_data(status)
            dfilter = status != 0

        field_cache = {}
        field_data = {}
        freg = re.compile(r"(^.+)_(\d+$)")
        for field in rfields:
            fs = freg.search(field)
            if fs and fs.groups()[0] in fh:
                fieldname, ifield = fs.groups()
                ifield = int(ifield)
                if fieldname not in field_cache:
                    field_cache[fieldname] = fh[fieldname][index]
                data = field_cache[fieldname][:, ifield]
            else:
                data = fh[field][index]
            field_data[field] = self._transform_data(
                data, my_filter=dfilter)

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

    def _transform_data(self, data, my_filter=None):
        data = np.flip(data, axis=0).flatten()
        if my_filter is not None:
            data = data[my_filter]
        return data

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
            if "Descendant" in fields:
                desc_uids = field_data["Descendant"].copy()
            else:
                desc_uids = field_data.pop("Descendant")
            desc_uids[desc_uids != -1] += root_node.uid
            adata["desc_uid"] = desc_uids

        return adata

class MoriaRootFieldIO(DefaultRootFieldIO):
    def _read_fields(self, storage_object, fields, dtypes=None):
        if dtypes is None:
            dtypes = {}

        data_file = self.arbor.data_files[0]
        data_file.open()
        fh = data_file.fh

        index = self.arbor._node_info['_si']
        field_cache = {}
        field_data = {}
        fi = self.arbor.field_info
        freg = re.compile(r"(^.+)_(\d+$)")
        for field in fields:
            if fi[field].get("vector", False):
                fs = freg.search(field)
                fieldname, ifield = fs.groups()
                ifield = int(ifield)
                if fieldname not in field_cache:
                    field_cache[fieldname] = fh[fieldname][-1][index]
                data = field_cache[fieldname][:, ifield]
            else:
                data = fh[field][-1][index]

            dtype = dtypes.get(field)
            if dtype is not None:
                data = data.astype(dtype)
            units = fi[field].get("units", "")
            if units != "":
                data = self.arbor.arr(data, units)
            field_data[field] = data

        fh.close()

        return field_data
