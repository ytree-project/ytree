"""
TreeFarmArbor io classes and member functions



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
    CatalogDataFile

class TreeFarmDataFile(CatalogDataFile):
    def open(self):
        self.fh = h5py.File(self.filename, "r")

    def _parse_header(self):
        self.open()
        fh = self.fh
        self.redshift = fh.attrs["current_redshift"]
        self.nhalos   = fh.attrs["num_halos"]
        # Files with no halos won't have the units.
        # Keep trying until we get one.
        if not hasattr(self.arbor, "field_list"):
            self._setup_field_info(fh)
        self.close()

    def _setup_field_info(self, fh):
        fields = list(fh.keys())
        fi = {}
        for field in fields:
            if fh[field].size == 0:
                # Zero-sized arrays won't have units, so don't bother.
                return
            units = fh[field].attrs["units"]
            if isinstance(units, bytes):
                units = units.decode("utf")
            fi[field] = {"source": "file", "units": units}

        fields.append("redshift")
        fi["redshift"] = {"source": "header", "units": ""}

        self.arbor.field_list = fields
        self.arbor.field_info.update(fi)

    def _read_data_default(self, rfields, dtypes):
        field_data = {}
        if not rfields:
            return field_data

        self.open()
        fh = self.fh
        field_data = dict((field, fh[field][()])
                          for field in rfields)
        self.close()

        for field in rfields:
            dtype = dtypes[field]
            field_data[field] = field_data[field].astype(dtype)
        return field_data

    def _read_data_select(self, rfields, tree_nodes, dtypes):
        field_data = {}
        if not rfields:
            return field_data

        file_ids = np.array([node._fi for node in tree_nodes])
        self.open()
        fh = self.fh
        for field in rfields:
            field_data[field] = fh[field][()][file_ids]
        self.close()

        for field in rfields:
            dtype = dtypes[field]
            field_data[field] = field_data[field].astype(dtype)
        return field_data
