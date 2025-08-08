"""
CSVArbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from ytree.data_structures.io import CatalogDataFile

class CSVDataFile(CatalogDataFile):
    def open(self):
        self.fh = open(self.filename, mode="r")

    def _parse_header(self):
        pass

    def _read_data_select(self, rfields, tree_nodes, dtypes):
        if not rfields:
            return {}

        fi = self.arbor.field_info
        nt = len(tree_nodes)
        field_data = \
          self._create_field_arrays(rfields, dtypes, size=nt)

        self.open()
        f = self.fh
        sep = self.arbor.sep
        for i, tree_node in enumerate(tree_nodes):
            f.seek(tree_node._offset)
            line = f.readline()
            sline = line.split(sep)
            for field in rfields:
                field_data[field][i] = sline[fi[field]["column"]]
        self.close()

        return field_data
