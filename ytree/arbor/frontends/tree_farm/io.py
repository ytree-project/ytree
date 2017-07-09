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

from collections import defaultdict
import h5py
import numpy as np

from ytree.arbor.io import \
    CatalogDataFile, \
    TreeFieldIO

class TreeFarmDataFile(CatalogDataFile):
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
