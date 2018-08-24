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

from ytree.arbor.io import \
    CatalogDataFile, \
    TreeFieldIO

class TreeFarmDataFile(CatalogDataFile):

    _default_dtype = np.float64

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

    def _read_fields(self, fields, tree_nodes=None, dtypes=None):
        if dtypes is None:
            dtypes = {}

        fi = self.arbor.field_info
        afields = [field for field in fields
                   if fi[field].get("source") == "arbor"]
        hfields = [field for field in fields
                   if fi[field].get("source") == "header"]
        rfields = set(fields).difference(afields + hfields)

        hfield_values = dict((field, getattr(self, field))
                             for field in hfields)

        if tree_nodes is None:
            ntrees = self.nhalos
            self.open()
            fh = self.fh
            field_data = dict((field, fh[field].value)
                              for field in rfields)
            self.close()

        else:
            ntrees = len(tree_nodes)
            file_ids = np.array([node._fi for node in tree_nodes])
            field_data = {}

            # fields from arbor-related info
            if afields:
                for field in afields:
                    field_data[field] = \
                      np.empty(ntrees, dtype=dtypes.get(field, self._default_dtype))
                for i in range(ntrees):
                    for field in afields:
                        field_data[field][i] = getattr(tree_nodes[i], field)

            if rfields:
                self.open()
                fh = self.fh
                for field in rfields:
                    field_data[field] = fh[field].value[file_ids]
                self.close()

        for field in hfields:
            field_data[field] = hfield_values[field] * \
              np.ones(ntrees, dtypes.get(field, self._default_dtype))
        for field in dtypes:
            if field in hfields: continue
            field_data[field] = field_data[field].astype(dtypes[field])

        return field_data

class TreeFarmTreeFieldIO(TreeFieldIO):

    _default_dtype = np.float64
