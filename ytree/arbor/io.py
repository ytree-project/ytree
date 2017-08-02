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

from collections import defaultdict
import numpy as np

from yt.funcs import \
    just_one

from ytree.utilities.exceptions import \
    ArborAnalysisFieldNotGenerated
from ytree.utilities.logger import \
    ytreeLogger as mylog

class FieldIO(object):
    """
    Base class for FieldIO classes.

    This object is resposible for field i/o for an Arbor.
    """

    def __init__(self, arbor):
        self.arbor = arbor

    def _initialize_analysis_field(self, storage_object,
                                   name, units, **kwargs):
        """
        Create a zero array of appropriate size to be filled in later.
        """
        raise NotImplementedError

    def _determine_field_storage(self, data_object, **kwargs):
        """
        Figure out which objects are responsible for storing field data.
        """
        raise NotImplementedError

    def _read_fields(self, *args, **kwargs):
        """
        Read fields from disk.
        """
        raise NotImplementedError

    def _store_fields(self, storage_object, field_data, **kwargs):
        """
        Store the field data in the proper place.
        """
        raise NotImplementedError

    def get_fields(self, data_object, fields=None, **kwargs):
        """
        Load field data for a data object into storage structures.
        """

        if fields is None or len(fields) == 0:
            return

        # hack to make sure root_only is False if this is not a root
        if isinstance(self, TreeFieldIO) and \
          not data_object.is_root:
            kwargs["root_only"] = False

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
            if fi[field].get("type") == "analysis":
                if field not in fields:
                    raise ArborAnalysisFieldNotGenerated(field, self.arbor)
                self._initialize_analysis_field(
                    storage_object, field, fi[field]["units"])
                continue
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
    """
    IO class for getting fields for a tree.
    """

    _default_dtype = np.float32

    def _initialize_analysis_field(self, storage_object,
                                   name, units, **kwargs):
        if name in storage_object._tree_field_data:
            return
        storage_object.arbor._setup_tree(storage_object)
        data = np.zeros(storage_object.uids.size)
        if units != "":
            data = self.arbor.arr(data, units)
        storage_object._tree_field_data[name] = data

    def _determine_field_storage(self, data_object, **kwargs):
        root_only = kwargs.get("root_only", True)

        if data_object.is_root:
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

class RootFieldIO(FieldIO):
    """
    IO class for getting fields for the roots of all trees.
    """

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

        fi = self.arbor.field_info

        fields_to_get = []
        for field in fields:
            if field not in data_object._root_field_data:
                if fi[field].get("type") == "analysis":
                    mylog.warn(
                        ("Accessing analysis field \"%s\" as root field. " +
                         "Any changes made will not be reflected here.") %
                         field)
                fields_to_get.append(field)
        if not fields_to_get:
            return

        if fields_to_get:
            self.arbor._node_io_loop(
                self.arbor._node_io.get_fields, pbar="Getting root fields",
                fields=fields_to_get, root_only=True)

        field_data = {}
        for field in fields_to_get:
            units = fi[field].get("units", "")
            field_data[field] = np.empty(self.arbor.trees.size)
            if units:
                field_data[field] = \
                  self.arbor.arr(field_data[field], units)
            for i in range(self.arbor.trees.size):
                if fi[field].get("type") == "analysis":
                    field_data[field][i] = \
                      self.arbor.trees[i]._tree_field_data[field][0]
                else:
                    field_data[field][i] = \
                      self.arbor.trees[i]._root_field_data[field]
        data_object._root_field_data.update(field_data)

class CatalogDataFile(object):
    """
    Base class for halo catalog files.
    """

    _default_dtype = np.float32

    def __init__(self, filename, arbor):
        self.filename = filename
        self.arbor = arbor
        self._parse_header()

    def _parse_header(self):
        raise NotImplementedError

    def _read_fields(self, *args, **kwargs):
        raise NotImplementedError

    def __repr__(self):
        return self.filename
