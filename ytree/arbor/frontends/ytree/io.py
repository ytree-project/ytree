"""
YTreeArbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016-2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py
import numpy as np

from ytree.arbor.io import \
    RootFieldIO, \
    TreeFieldIO

class YTreeTreeFieldIO(TreeFieldIO):
    def _read_fields(self, root_node, fields, dtypes=None,
                     f=None, root_only=False):
        if dtypes is None:
            dtypes = {}

        if f is None:
            close = True
            fi = np.digitize(root_node._ai, self.arbor._ei)
            fn = "%s_%04d%s" % (self.arbor._prefix, fi, self.arbor._suffix)
            fh = h5py.File(fn, "r")
        else:
            close = False

        start_index = fh["index/tree_start_index"].value
        end_index   = fh["index/tree_end_index"].value
        ii = root_node._ai - self.arbor._si[fi]

        field_data = {}
        fi = self.arbor.field_info
        for field in fields:
            data = fh["data/%s" % field][start_index[ii]:end_index[ii]]
            dtype = dtypes.get(field)
            if dtype is not None:
                data = data.astype(dtype)
            units = fi[field].get("units", "")
            if units != "":
                data = self.arbor.arr(data, units)
            field_data[field] = data

        if close:
            fh.close()

        return field_data

class YTreeRootFieldIO(RootFieldIO):
    def _read_fields(self, storage_object, fields, dtypes=None):
        if dtypes is None:
            dtypes = {}

        fh = h5py.File(self.arbor.filename, "r")
        field_data = {}
        fi = self.arbor.field_info
        for field in fields:
            data = fh["data/%s" % field].value
            dtype = dtypes.get(field)
            if dtype is not None:
                data = data.astype(dtype)
            units = fi[field].get("units", "")
            if units != "":
                data = self.arbor.arr(data, units)
            field_data[field] = data
        fh.close()

        return field_data
