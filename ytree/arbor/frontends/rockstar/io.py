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
    TreeFieldIO
from ytree.arbor.frontends.rockstar.misc import \
    f_text_block

class RockstarDataFile(object):
    def __init__(self, filename, arbor):
        self.filename = filename
        self.arbor = arbor
        self.offsets = None
        self._parse_header()

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
        if tree_nodes is not None:
            raise NotImplementedError

        my_dtypes = dict((field, np.float32) for field in fields)
        if dtypes is None:
            dtypes = {}
        my_dtypes.update(dtypes)

        fi = self.arbor.field_info
        field_data = dict((field, []) for field in fields)

        offsets = []
        f = open(self.filename, "r")
        f.seek(self._hoffset)
        file_size = self.file_size - self._hoffset
        for line, offset in f_text_block(f, file_size=file_size):
            offsets.append(offset)
            sline = line.split()
            for field in fields:
                field_data[field].append(
                  my_dtypes[field](sline[fi[field]["column"]]))
        f.close()
        if self.offsets is None:
            self.offsets = np.array(offsets)
        return field_data

class RockstarTreeFieldIO(TreeFieldIO):
    def _read_fields(self, root_node, fields, dtypes=None,
                     f=None, root_only=False):
        """
        Read fields from disk for a single tree.
        """
        if dtypes is None:
            dtypes = {}

        raise NotImplementedError

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
