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
    field_cache = None
    full_read = False
    fh = None

    def open(self):
        self.fh = h5py.File(self.filename, mode="r")

    def close(self):
        self.fh.close()
        self.fh = None

    def read_data(self, field, index):
        if self.full_read:
            if self.field_cache is None:
                self.field_cache = {}

            if field not in self.field_cache:
                self.field_cache[field] = self.fh[field][()]
            return self.field_cache[field][index]
        else:
            return self.fh[field][index]

class MoriaTreeFieldIO(TreeFieldIO):

    def get_fields(self, data_object, fields=None, **kwargs):
        """
        Call _setup_tree if asking for desc_uid so we can correct it.
        """

        if fields is not None and "desc_uid" in fields:
            self.arbor._setup_tree(data_object)
        super().get_fields(data_object, fields=fields, **kwargs)

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

        if root_only:
            index = (-1, slice(root_node._si, root_node._si+1))
            dfilter = None
        else:
            index = (slice(None), slice(root_node._si, root_node._ei))
            if not hasattr(root_node, "_status"):
                status = data_file.read_data("status_sparta", index)
                status = self._transform_data(status)
                root_node._status = np.where(status != 0)[0]
            dfilter = root_node._status

        # this field cache is for temporarily storing vector field data
        field_cache = {}
        field_data = {}
        freg = re.compile(r"(^.+)_(\d+$)")
        for field in rfields:
            if fi[field].get("vector", False):
                fs = freg.search(field)
                fieldname, ifield = fs.groups()
                ifield = int(ifield)
                if fieldname not in field_cache:
                    field_cache[fieldname] = data_file.read_data(fieldname, index)
                data = field_cache[fieldname][..., ifield]
            else:
                data = data_file.read_data(field, index)
            field_data[field] = self._transform_data(
                data, my_filter=dfilter)

        if afields:
            field_data.update(self._get_arbor_fields(
                root_node, field_data, fields, afields, root_only,
                my_filter=dfilter))

        if close:
            data_file.close()

        self._apply_units(rfields, field_data)

        return field_data

    def _transform_data(self, data, my_filter=None):
        data = np.flip(data, axis=0).flatten()
        if my_filter is not None:
            data = data[my_filter]
        return data

    def _get_arbor_fields(self, root_node, field_data,
                          fields, afields, root_only,
                          my_filter=None):
        """
        Generate special fields from the arbor/treenode.
        """

        adata = {}

        if "snap_index" in fields:
            if root_only:
                adata["snap_index"] = \
                  np.array([self.arbor._redshifts.size-1], dtype=int)
            else:
                data, _ = np.mgrid[:self.arbor._redshifts.size,
                                   root_node._si:root_node._ei]
                adata["snap_index"] = self._transform_data(
                    data, my_filter=my_filter)

        return adata

class MoriaRootFieldIO(DefaultRootFieldIO):
    def _read_fields(self, storage_object, fields, dtypes=None):
        self.arbor._plant_trees()

        if dtypes is None:
            dtypes = {}

        fi = self.arbor.field_info
        afields = [field for field in fields
                   if fi[field].get("source") == "arbor"]
        rfields = list(set(fields).difference(afields))

        for afield in afields:
            rfields.extend(
                [dfield for dfield in fi[afield].get("dependencies", [])
                 if dfield not in rfields])

        data_file = self.arbor.data_files[0]
        data_file.open()
        fh = data_file.fh

        index = self.arbor._node_info['_si']
        field_cache = {}
        field_data = {}
        freg = re.compile(r"(^.+)_(\d+$)")
        for field in rfields:
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
            field_data[field] = data

        self._apply_units(rfields, field_data)

        if afields:
            field_data.update(self._get_arbor_fields(
                field_data, fields, afields))

        data_file.close()

        return field_data

    def _get_arbor_fields(self, field_data, fields, afields):
        adata = {}

        if "snap_index" in fields:
            adata["snap_index"] = \
              np.full(self.arbor.size, self.arbor._redshifts.size-1)

        return adata
