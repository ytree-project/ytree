"""
YTreeArbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
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
                     f=None, root_only=False, fcache=None):
        if dtypes is None:
            dtypes = {}

        if fcache is None:
            fcache = {}

        dfi = np.digitize(root_node._ai, self.arbor._ei)
        if f is None:
            close = True
            fn = "%s_%04d%s" % (self.arbor._prefix, dfi, self.arbor._suffix)
            f = h5py.File(fn, "r")
        else:
            close = False

        start_index = f["index/tree_start_index"].value
        end_index   = f["index/tree_end_index"].value
        ii = root_node._ai - self.arbor._si[dfi]

        field_data = {}
        fi = self.arbor.field_info
        for field in fields:
            if field not in fcache:
                fdata = f["data/%s" % field].value
                dtype = dtypes.get(field)
                if dtype is not None:
                    fdata = fdata.astype(dtype)
                units = fi[field].get("units", "")
                if units != "":
                    fdata = self.arbor.arr(fdata, units)
                fcache[field] = fdata
            field_data[field] = \
              fcache[field][start_index[ii]:end_index[ii]]

        if close:
            f.close()

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
