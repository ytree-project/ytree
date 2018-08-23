"""
YTreeArbor io classes and member functions



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

from ytree.arbor.io import \
    DataFile, \
    FieldIO, \
    TreeFieldIO

class YTreeDataFile(DataFile):
    def __init__(self, filename):
        super(YTreeDataFile, self).__init__(filename)
        self._field_cache = None
        self._start_index = None
        self._end_index = None

    def open(self):
        self.fh = h5py.File(self.filename, "r")

class YTreeTreeFieldIO(TreeFieldIO):
    def _read_fields(self, root_node, fields, dtypes=None, root_only=False):
        dfi = np.digitize(root_node._ai, self._ei)
        data_file = self.data_files[dfi]

        if dtypes is None:
            dtypes = {}

        if data_file._field_cache is None:
            data_file._field_cache = {}

        if data_file.fh is None:
            close = True
            data_file.open()
        else:
            close = False

        # get start_index and end_index
        for itype in ["start", "end"]:
            if getattr(data_file, "_%s_index" % itype) is None:
                setattr(data_file, "_%s_index" % itype,
                        data_file.fh["index/tree_%s_index" % itype].value)
        ii = root_node._ai - self._si[dfi]

        field_data = {}
        fi = self.arbor.field_info
        for field in fields:
            if field not in data_file._field_cache:
                fdata = data_file.fh["data/%s" % field].value
                dtype = dtypes.get(field)
                if dtype is not None:
                    fdata = fdata.astype(dtype)
                units = fi[field].get("units", "")
                if units != "":
                    fdata = self.arbor.arr(fdata, units)
                data_file._field_cache[field] = fdata
            field_data[field] = \
              data_file._field_cache[field][
                  data_file._start_index[ii]:data_file._end_index[ii]]

        if close:
            data_file.close()

        return field_data

class YTreeRootFieldIO(FieldIO):
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

    def _initialize_analysis_field(self, storage_object,
                                   name, units, **kwargs):
        # Always refresh this because it may have changed.
        if name in storage_object._field_data:
            data = storage_object._field_data[name]
        else:
            data = np.zeros(storage_object.size)
            if units != "":
                data = self.arbor.arr(data, units)
            storage_object._field_data[name] = data

        for i, halo in enumerate(storage_object):
            data[i] = halo[name]
