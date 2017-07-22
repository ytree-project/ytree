"""
RockstarArbor io classes and member functions



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
    CatalogDataFile
from ytree.arbor.frontends.rockstar.misc import \
    f_text_block

class RockstarDataFile(CatalogDataFile):
    def __init__(self, filename, arbor):
        self.offsets = None
        super(RockstarDataFile, self).__init__(filename, arbor)

    def _parse_header(self):
        f = open(self.filename, "r")
        f.seek(0, 2)
        self.file_size = f.tell()
        f.seek(0)
        while True:
            line = f.readline()
            if line is None:
                self._hoffset = f.tell()
                break
            elif not line.startswith("#"):
                self._hoffset = f.tell() - len(line)
                break
            elif line.startswith("#a = "):
                self.scale_factor = float(line.split(" = ")[1])
        f.close()

    def _read_fields(self, fields, tree_nodes=None, dtypes=None):
        if dtypes is None:
            dtypes = {}

        fi = self.arbor.field_info
        hfields = [field for field in fields
                   if fi[field]["column"] == "header"]
        rfields = set(fields).difference(hfields)

        hfield_values = dict((field, getattr(self, field))
                             for field in hfields)

        if tree_nodes is None:
            field_data = dict((field, []) for field in fields)
            offsets = []
            f = open(self.filename, "r")
            f.seek(self._hoffset)
            file_size = self.file_size - self._hoffset
            for line, offset in f_text_block(f, file_size=file_size):
                offsets.append(offset)
                sline = line.split()
                for field in hfields:
                    field_data[field].append(hfield_values[field])
                for field in rfields:
                    dtype = dtypes.get(field, self._default_dtype)
                    field_data[field].append(dtype(sline[fi[field]["column"]]))
            f.close()
            if self.offsets is None:
                self.offsets = np.array(offsets)

        else:
            ntrees = len(tree_nodes)
            field_data = \
              dict((field,
                    np.empty(ntrees,
                             dtype=dtypes.get(field, self._default_dtype)))
                    for field in fields)

            # fields from the file header
            for field in hfields:
                field_data[field][:] = hfield_values[field]

            # fields from the actual data
            f = open(self.filename, "r")
            for i in range(ntrees):
                f.seek(self.offsets[tree_nodes[i]._fi])
                line = f.readline()
                sline = line.split()
                for field in rfields:
                    dtype = dtypes.get(field, self._default_dtype)
                    field_data[field][i] = dtype(sline[fi[field]["column"]])
            f.close()

        return field_data
