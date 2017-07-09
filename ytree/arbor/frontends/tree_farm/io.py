"""
TreeFarmArbor io classes and member functions



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
    CatalogDataFile, \
    TreeFieldIO

class TreeFarmDataFile(CatalogDataFile):

    _default_dtype = np.float64

    def _parse_header(self):
        fh = h5py.File(self.filename, "r")
        self.redshift = fh.attrs["current_redshift"]
        self.nhalos   = fh.attrs["num_halos"]
        fh.close()

    def _read_fields(self, fields, tree_nodes=None, dtypes=None):
        if dtypes is None:
            dtypes = {}

        fi = self.arbor.field_info
        hfields = [field for field in fields
                   if fi[field]["source"] == "header"]
        rfields = set(fields).difference(hfields)

        hfield_values = dict((field, getattr(self, field))
                             for field in hfields)

        if tree_nodes is None:
            ntrees = self.nhalos
            fh = h5py.File(self.filename, "r")
            field_data = dict((field, fh[field].value)
                              for field in rfields)
            fh.close()

        else:
            ntrees = len(tree_nodes)
            file_ids = np.array([node._fi for node in tree_nodes])
            field_data = {}
            fh = h5py.File(self.filename, "r")
            for field in rfields:
                field_data[field] = fh[field].value[file_ids]
            fh.close()

        for field in hfields:
            field_data[field] = hfield_values[field] * \
              np.ones(ntrees, dtypes.get(field, self._default_dtype))
        for field in dtypes:
            if field in hfields: continue
            field_data[field] = field_data[field].astype(dtypes[field])

        return field_data

class TreeFarmTreeFieldIO(TreeFieldIO):

    _default_dtype = np.float64
