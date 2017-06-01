"""
ConsistentTreesArbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from ytree.arbor.io import \
    TreeFieldIO

class ConsistentTreesTreeFieldIO(TreeFieldIO):
    def _read_fields(self, root_node, fields, dtypes=None,
                     f=None, root_only=False):
        """
        Read fields from disk for a single tree.
        """
        if dtypes is None:
            dtypes = {}

        close = False
        if f is None:
            close = True
            f = open(self.arbor.filename, "r")
        f.seek(root_node._si)
        if root_only:
            data = [f.readline()]
        else:
            data = f.read(
                root_node._ei -
                root_node._si).split("\n")
            if len(data[-1]) == 0:
                data.pop()
        if close:
            f.close()

        nhalos = len(data)
        field_data = {}
        fi = self.arbor.field_info
        for field in fields:
            field_data[field] = \
              np.empty(nhalos, dtype=dtypes.get(field, float))

        for i, datum in enumerate(data):
            ldata = datum.strip().split()
            if len(ldata) == 0: continue
            for field in fields:
                dtype = dtypes.get(field, float)
                field_data[field][i] = dtype(ldata[fi[field]["column"]])

        for field in fields:
            units = fi[field].get("units", "")
            if units != "":
                field_data[field] = \
                  self.arbor.arr(field_data[field], units)

        return field_data
