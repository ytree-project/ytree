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

from collections import defaultdict
import numpy as np

from ytree.arbor.io import \
    TreeFieldIO
from ytree.arbor.frontends.rockstar.misc import \
    f_text_block

class RockstarDataFile(object):

    _default_dtype = np.float32

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
        if dtypes is None:
            dtypes = {}

        fi = self.arbor.field_info
        hfields = [field for field in fields
                   if fi[field]["column"] == "header"]
        rfields = set(fields).difference(hfields)

        hfield_values = dict((field, getattr(self, field))
                             for field in hfields)

        if tree_nodes is not None:
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

        else:
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

        return field_data

class RockstarTreeFieldIO(TreeFieldIO):

    _default_dtype = np.float32

    def _read_fields(self, root_node, fields, dtypes=None,
                     root_only=False):
        """
        Read fields from disk for a single tree.
        """

        if dtypes is None:
            dtypes = {}

        nhalos = root_node.tree_size
        field_data = {}
        for field in fields:
            field_data[field] = \
              np.empty(nhalos, dtype=dtypes.get(field, self._default_dtype))

        if root_only:
            my_nodes = [root_node]
        else:
            my_nodes = root_node.nodes

        data_files = defaultdict(list)
        for node in my_nodes:
            data_files[node.data_file].append(node)

        for data_file, nodes in data_files.items():
            my_data = data_file._read_fields(fields, tree_nodes=nodes,
                                             dtypes=dtypes)
            for field in fields:
                for i, node in enumerate(nodes):
                    field_data[field][node.treeid] = my_data[field][i]

        fi = self.arbor.field_info
        for field in fields:
            units = fi[field].get("units", "")
            if units != "":
                field_data[field] = \
                  self.arbor.arr(field_data[field], units)

        return field_data
