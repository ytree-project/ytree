"""
ArborArbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py

from ytree.arbor.io import \
    FieldIO, \
    TreeFieldIO

class ArborArborTreeFieldIO(TreeFieldIO):
    def _read_fields(self, root_node, fields, dtypes=None,
                     f=None, root_only=False, fcache=None):
        if dtypes is None:
            dtypes = {}

        if fcache is None:
            fcache = {}

        if f is None:
            close = True
            f = h5py.File(self.arbor.filename, "r")
        else:
            close = False

        ifield = root_node._fi

        field_data = {}
        fi = self.arbor.field_info
        for field in fields:
            if field not in fcache:
                if field in self.arbor._field_cache:
                    rdata = self.arbor._field_cache[field]
                else:
                    if fi[field].get("vector", False):
                        rfield, ax = field.rsplit("_", 1)
                        rdata = f["data/%s" % rfield][:, "xyz".find(ax)]
                    else:
                        rdata = f["data/%s" % field].value
                    dtype = dtypes.get(field)
                    if dtype is not None:
                        rdata = rdata.astype(dtype)
                    units = fi[field].get("units", "")
                    if units != "":
                        rdata = self.arbor.arr(rdata, units)
                    self.arbor._field_cache[field] = rdata
                fcache[field] = rdata[ifield]
            field_data[field] = fcache[field]

        if close:
            f.close()

        return field_data

class ArborArborRootFieldIO(FieldIO):
    def _read_fields(self, storage_object, fields, dtypes=None):
        if dtypes is None:
            dtypes = {}
        self.arbor.trees

        fcache = storage_object._field_data

        fh = h5py.File(self.arbor.filename, "r")
        field_data = {}
        fi = self.arbor.field_info
        for field in fields:
            if field not in fcache:
                if field in self.arbor._field_cache:
                    rdata = self.arbor._field_cache[field]
                else:
                    if fi[field].get("vector", False):
                        rfield, ax = field.rsplit("_", 1)
                        rdata = fh["data/%s" % rfield][:, "xyz".find(ax)]
                    else:
                        rdata = fh["data/%s" % field].value
                    dtype = dtypes.get(field)
                    if dtype is not None:
                        rdata = rdata.astype(dtype)
                    units = fi[field].get("units", "")
                    if units != "":
                        rdata = self.arbor.arr(rdata, units)
                    self.arbor._field_cache[field] = rdata
                fcache[field] = rdata[self.arbor._ri]
            field_data[field] = fcache[field]
        fh.close()

        return field_data
