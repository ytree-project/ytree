"""
CSVArbor io classes and member functions



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from ytree.data_structures.io import CatalogDataFile


class CSVDataFile(CatalogDataFile):
    def open(self):
        self.fh = open(self.filename, mode="r")

    def _parse_header(self):
        pass

    def _read_data_select(self, rfields, tree_nodes, dtypes):
        if not rfields:
            return {}

        # We want to support nodes with missing descendents,
        # but this requires we manually reset their desc_uid to -1.
        reset_desc_uid = "desc_uid" in rfields

        fi = self.arbor.field_info
        nt = len(tree_nodes)
        field_data = self._create_field_arrays(rfields, dtypes, size=nt)

        self.open()
        f = self.fh
        sep = self.arbor.sep
        for i, tree_node in enumerate(tree_nodes):
            f.seek(tree_node._offset)
            line = f.readline()
            sline = line.split(sep)
            for field in rfields:
                field_data[field][i] = sline[fi[field]["column"]]

            if reset_desc_uid and tree_node.is_root:
                field_data["desc_uid"][i] = -1
        self.close()

        return field_data
