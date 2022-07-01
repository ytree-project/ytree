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

from ytree.data_structures.io import \
    DefaultRootFieldIO, \
    DataFile, \
    TreeFieldIO

class YTreeDataFile(DataFile):
    def __init__(self, filename):
        super().__init__(filename)
        self._field_cache = None
        self._start_index = None
        self._end_index = None

    def open(self):
        self.fh = h5py.File(self.filename, mode="r")
        if hasattr(self, "analysis_filename"):
            self.analysis_fh = h5py.File(self.analysis_filename, mode="r")

    def close(self):
        self.fh.close()
        self.fh = None
        if hasattr(self, "analysis_filename"):
            self.analysis_fh.close()
            self.analysis_fh = None

class YTreeTreeFieldIO(TreeFieldIO):
    def _read_fields(self, root_node, fields, dtypes=None, root_only=False):
        dfi = np.digitize(root_node._ai, self._ei)
        data_file = self.arbor.data_files[dfi]

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
            if getattr(data_file, f"_{itype}_index") is None:
                setattr(data_file, f"_{itype}_index",
                        data_file.fh[f"index/tree_{itype}_index"][()])
        ii = root_node._ai - self._si[dfi]

        field_data = {}
        fi = self.arbor.field_info
        for field in fields:
            if field not in data_file._field_cache:
                if fi[field].get("type") == "analysis_saved":
                    fh = data_file.analysis_fh
                else:
                    fh = data_file.fh
                fdata = fh[f"data/{field}"][()]

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

class YTreeRootFieldIO(DefaultRootFieldIO):
    def _read_fields(self, storage_object, fields, dtypes=None):
        if dtypes is None:
            dtypes = {}

        fh = h5py.File(self.arbor.filename, mode="r")
        if self.arbor.analysis_filename is not None:
            analysis_fh = h5py.File(self.arbor.analysis_filename, mode="r")

        field_data = {}
        fi = self.arbor.field_info
        for field in fields:
            if fi[field].get("type") == "analysis_saved":
                my_fh = analysis_fh
            else:
                my_fh = fh
            data = my_fh[f"data/{field}"][()]
            dtype = dtypes.get(field)
            if dtype is not None:
                data = data.astype(dtype)
            field_data[field] = data

        self._apply_units(fields, field_data)

        fh.close()
        if self.arbor.analysis_filename is not None:
            analysis_fh.close()

        return field_data
