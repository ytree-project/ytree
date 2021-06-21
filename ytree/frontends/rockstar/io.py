"""
RockstarArbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from ytree.data_structures.io import \
    CatalogDataFile
from ytree.utilities.io import \
    f_text_block

class RockstarDataFile(CatalogDataFile):
    def __init__(self, filename, arbor):
        self.offsets = None
        super().__init__(filename, arbor)

    def open(self):
        self.fh = open(self.filename, "r")

    def _parse_header(self):
        self.open()
        f = self.fh
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
        self.close()

    def _read_data_default(self, rfields, dtypes):
        if not rfields:
            return {}

        fi = self.arbor.field_info
        field_data = \
          self._create_field_arrays(rfields, dtypes)
        offsets = []

        self.open()
        f = self.fh
        f.seek(self._hoffset)
        file_size = self.file_size - self._hoffset
        for line, offset in f_text_block(f, file_size=file_size):
            offsets.append(offset)
            sline = line.split()
            for field in rfields:
                field_data[field].append(sline[fi[field]["column"]])
        self.close()

        for field in rfields:
            field_data[field] = \
              np.array(field_data[field], dtype=dtypes[field])

        if self.offsets is None:
            self.offsets = np.array(offsets)

        return field_data

    def _read_data_select(self, rfields, tree_nodes, dtypes):
        if not rfields:
            return {}

        fi = self.arbor.field_info
        nt = len(tree_nodes)
        field_data = \
          self._create_field_arrays(rfields, dtypes, size=nt)

        self.open()
        f = self.fh
        for i in range(nt):
            f.seek(self.offsets[tree_nodes[i]._fi])
            line = f.readline()
            sline = line.split()
            for field in rfields:
                dtype = dtypes[field]
                field_data[field][i] = dtype(sline[fi[field]["column"]])
        self.close()

        return field_data
