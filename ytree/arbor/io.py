"""
FieldIO class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from yt.funcs import \
    just_one

class FieldIO(object):
    """
    Base class for FieldIO classes.

    This object is resposible for field i/o for an Arbor.
    """

    def __init__(self, arbor):
        self.arbor = arbor

    def _determine_field_storage(self, data_object, **kwargs):
        """
        Figure out which objects are responsible for storing field data.
        """
        pass

    def _store_fields(self, storage_object, field_data, **kwargs):
        """
        Store the field data in the proper place.
        """
        pass

    def get_fields(self, data_object, fields=None, **kwargs):
        """
        Load field data for a data object into storage structures.
        """

        if fields is None or len(fields) == 0:
            return

        storage_object, fcache = \
          self._determine_field_storage(data_object, **kwargs)

        fi = self.arbor.field_info

        # Resolve field dependencies.
        fields_to_read, fields_to_generate = \
          fi.resolve_field_dependencies(fields, fcache=fcache)

        # Read in fields we need that are on disk.
        if fields_to_read:
            field_data = self._read_fields(
                storage_object, fields_to_read, **kwargs)
            self._store_fields(storage_object, field_data, **kwargs)

        # Generate all derived fields/aliases, but
        # only after dependencies have been generated.
        while len(fields_to_generate) > 0:
            field = fields_to_generate.pop(0)
            deps = set(fi[field]["dependencies"])
            need = deps.difference(fcache)
            # have not created all dependencies yet, try again later
            if need:
                fields_to_generate.append(field)
            # all dependencies present, generate the field
            else:
                units = fi[field].get("units")
                ftype = fi[field]["type"]
                if ftype == "alias":
                    data = fcache[fi[field]["dependencies"][0]]
                elif ftype == "derived":
                    data = fi[field]["function"](fcache)
                if hasattr(data, "units") and units is not None:
                    data.convert_to_units(units)
                fdata = {field: data}
                self._store_fields(storage_object, fdata, **kwargs)

class TreeFieldIO(FieldIO):
    def _determine_field_storage(self, data_object, **kwargs):
        root_only = kwargs.get("root_only", True)

        if data_object.root == -1:
            storage_object = data_object
        else:
            storage_object = data_object.root
            root_only = False

        if root_only:
            fcache = storage_object._root_field_data
        else:
            fcache = storage_object._tree_field_data

        return storage_object, fcache

    def _store_fields(self, storage_object, field_data, **kwargs):
        root_only = kwargs.get("root_only", True)

        if not field_data: return
        root_field_data = dict(
            [(field, just_one(field_data[field]))
             for field in field_data])
        if not root_only:
            storage_object._tree_field_data.update(field_data)
        storage_object._root_field_data.update(root_field_data)

class RootFieldIO(FieldIO):
    def _determine_field_storage(self, data_object, **kwargs):
        return data_object, data_object._root_field_data

    def _store_fields(self, storage_object, field_data, **kwargs):
        storage_object._root_field_data.update(field_data)

class FallbackRootFieldIO(FieldIO):
    """
    Class for getting root fields from arbors that have no
    specialized storage for root fields.
    """

    def get_fields(self, data_object, fields=None):
        if fields is None or len(fields) == 0:
            return

        fields_to_read = []
        for field in fields:
            if field not in data_object._root_field_data:
                fields_to_read.append(field)
        if not fields_to_read:
            return

        self.arbor._node_io_loop(
            self.arbor._node_io.get_fields, pbar="Getting root fields",
            fields=fields_to_read, root_only=True)

        field_data = {}
        fi = self.arbor.field_info
        for field in fields_to_read:
            units = fi[field].get("units", "")
            field_data[field] = np.empty(self.arbor.trees.size)
            if units:
                field_data[field] = \
                  self.arbor.arr(field_data[field], units)
            for i in range(self.arbor.trees.size):
                field_data[field][i] = \
                  self.arbor.trees[i]._root_field_data[field]
        data_object._root_field_data.update(field_data)

