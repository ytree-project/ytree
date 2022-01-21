"""
FieldIO class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from collections import defaultdict
import numpy as np
import os
from unyt import uconcatenate
import weakref

from ytree.utilities.exceptions import \
    ArborAnalysisFieldNotGenerated
from ytree.utilities.logger import \
    ytreeLogger as mylog

class FieldIO:
    """
    Base class for FieldIO classes.

    This object is resposible for field i/o for an Arbor.
    """

    def __init__(self, arbor, default_dtype=np.float64):
        self.arbor = weakref.proxy(arbor)
        self.default_dtype = default_dtype

    def _apply_units(self, fields, field_data):
        """
        Apply units to data that's just been read in.
        """

        fi = self.arbor.field_info
        for field in fields:
            units = fi[field].get("units", "")
            if units != "":
                field_data[field] = \
                  self.arbor.arr(field_data[field], units)

    def _initialize_analysis_field(self, storage_object, name):
        """
        Initialize an empty field array to be filled in later.
        """
        raise NotImplementedError

    def _determine_dtypes(self, fields, override_dict=None):
        """
        Figure out dtype for field.

        Priority is:
        1. override_dict
        2. self.arbor.field_info
        3. self.arbor.field_info._data_types
        4. self.default_dtype
        """
        if override_dict is None:
            override_dict = {}
        dtypes = override_dict.copy()

        fi = self.arbor.field_info
        fid = fi._data_types
        for field in fields:
            dtypes[field] = \
              dtypes.get(field, fi[field].get('dtype',
                fid.get(field, self.default_dtype)))
        return dtypes

    def _determine_field_storage(self, data_object):
        """
        Figure out which objects are responsible for storing field data.
        """
        return data_object

    def _read_fields(self, *args, **kwargs):
        """
        Read fields from disk.
        """
        raise NotImplementedError

    def _store_fields(self, storage_object, fields):
        """
        Only keep items on the fields list.
        """
        fcache = storage_object.field_data
        remove = set(fcache).difference(fields)
        for field in remove:
            del fcache[field]

    def get_fields(self, data_object, fields=None, **kwargs):
        """
        Load field data for a data object into storage structures.
        """

        if not fields:
            return

        # hack to make sure root_only is False if this is not a root
        if isinstance(self, TreeFieldIO) and \
          not data_object.is_root:
            kwargs["root_only"] = False

        storage_object = \
          self._determine_field_storage(data_object)
        fcache = storage_object.field_data

        fi = self.arbor.field_info

        # Determine size of field array we need.
        # Set to None if root_only since any size will do.
        if not hasattr(data_object, "root") or \
          kwargs.get("root_only", False):
            fsize = None
        else:
            if data_object.is_root:
                root = data_object
            else:
                root = data_object.find_root()
            fsize = root.tree_size

        # Resolve field dependencies.
        fields_to_read, fields_to_generate = \
          fi.resolve_field_dependencies(fields, fcache=fcache,
                                        fsize=fsize)

        # Keep list of fields present before getting new ones.
        # We need to do this after trees have been setup since
        # that will add fields to the field cache in some cases.
        old_fields = list(fcache.keys())

        # Read in fields we need that are on disk.
        if fields_to_read:
            read_data = self._read_fields(
                storage_object, fields_to_read, **kwargs)
            fcache.update(read_data)

        # Generate all derived fields/aliases, but
        # only after dependencies have been generated.
        while len(fields_to_generate) > 0:
            field = fields_to_generate.pop(0)
            if fi[field].get("type") == "analysis":
                if field not in fields:
                    raise ArborAnalysisFieldNotGenerated(field, self.arbor)
                self._initialize_analysis_field(storage_object, field)
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
                    data = fi[field]["function"](fi[field], fcache)
                if hasattr(data, "units") and units is not None:
                    data.convert_to_units(units)
                fcache[field] = data

        self._store_fields(storage_object, set(old_fields).union(fields))
        return storage_object.field_data

class TreeFieldIO(FieldIO):
    """
    IO class for getting fields for a tree.
    """

    def _initialize_analysis_field(self, storage_object, name):
        if name in storage_object.field_data:
            return
        fi = self.arbor.field_info[name]
        units = fi.get('units', '')
        dtype = fi.get('dtype', self.default_dtype)
        value = fi.get('default', 0)
        data = np.full(storage_object.tree_size, value, dtype=dtype)
        if units:
            data = self.arbor.arr(data, units)
        storage_object.field_data[name] = data

    def _determine_field_storage(self, data_object):
        return data_object.find_root()

    def _read_fields(self, root_node, fields, dtypes=None,
                     root_only=False):
        """
        Read fields from disk for a single tree.
        """

        if dtypes is None:
            dtypes = {}
        my_dtypes = self._determine_dtypes(
            fields, override_dict=dtypes)

        if root_only:
            fsize = 1
        else:
            fsize = root_node.tree_size

        field_data = {}
        for field in fields:
            field_data[field] = \
              np.empty(fsize, dtype=my_dtypes[field])

        if root_only:
            my_nodes = [root_node]
        else:
            my_nodes = root_node._tree_nodes

        data_files = defaultdict(list)
        for node in my_nodes:
            data_files[node.data_file].append(node)

        for data_file, nodes in data_files.items():
            my_data = data_file._read_fields(fields, tree_nodes=nodes,
                                             dtypes=my_dtypes)
            for field in fields:
                for i, node in enumerate(nodes):
                    field_data[field][node.tree_id] = my_data[field][i]

        self._apply_units(fields, field_data)

        return field_data

class DefaultRootFieldIO(FieldIO):
    """
    Class for getting root fields from arbors that have no
    specialized storage for root fields.
    """

    def _initialize_analysis_field(self, storage_object, name):
        fi = self.arbor.field_info[name]
        default = fi['default']
        dtype   = fi['dtype']
        units   = fi['units']

        storage_object.field_data[name] = \
          self.arbor.arr(np.full(self.arbor.size, default, dtype=dtype), units)

    def _read_fields(self, storage_object, fields, dtypes=None,
                     root_only=True):
        if not fields:
            return

        if dtypes is None:
            dtypes = {}
        my_dtypes = self._determine_dtypes(
            fields, override_dict=dtypes)

        rvals = self.arbor._node_io_loop(
            self.arbor._node_io._read_fields,
            pbar="Reading root fields",
            fields=fields, dtypes=my_dtypes, root_only=True)

        field_data = \
          dict((field, uconcatenate([fvals[field] for fvals in rvals]))
               for field in fields)

        return field_data

class DataFile:
    """
    Base class for data files.

    This class allows us keep files open during i/o heavy operations
    and to keep things like caches of fields.
    """
    def __init__(self, filename):
        if not os.path.exists(filename):
            mylog.warning(
                f"Cannot find data file: {filename}. "
                 "Will not be able to load field data.")

        self.filename = filename
        self.fh = None

    def __repr__(self):
        return self.filename

    def open(self):
        raise NotImplementedError

    def close(self):
        if self.fh is not None:
            self.fh.close()
            self.fh = None


# A dict of arbor field generators.
arbor_fields = {}
arbor_fields['uid'] = lambda t: t.uid
# This will only be called for a root.
arbor_fields['desc_uid'] = lambda t: -1 if t.descendent is None \
  else t.descendent.uid

class CatalogDataFile(DataFile):
    """
    Base class for halo catalog files.
    """

    def __init__(self, filename, arbor):
        super().__init__(filename)
        self.arbor = weakref.proxy(arbor)
        self._parse_header()

    def _parse_header(self):
        """
        Load any relevant data from the file header.
        """
        raise NotImplementedError

    def _get_field_sources(self, fields):
        """
        Distinguish field sources.

        Distinguish fields to be read from disk, from the file header,
        and from arbor properties.
        """

        fi = self.arbor.field_info
        afields = [field for field in fields
                   if fi[field].get("source") == "arbor"]
        hfields = [field for field in fields
                   if fi[field].get("source") == "header"]
        rfields = set(fields).difference(hfields + afields)

        return afields, hfields, rfields

    def _create_field_arrays(self, fields, dtypes, size=None):
        """
        Initialize empty field arrays.
        """

        if size is None:
            field_data = dict((field, []) for field in fields)

        else:
            field_data = \
              dict((field, np.empty(size, dtype=dtypes[field]))
                   for field in fields)

        return field_data

    def _get_arbor_fields(self, afields, tree_nodes, dtypes):
        """
        Get fields from arbor/tree_node properties.
        """

        if not afields:
            return {}

        nt = len(tree_nodes)
        field_data = self._create_field_arrays(afields, dtypes, size=nt)

        for field in afields:
            for i in range(nt):
                field_data[field][i] = \
                  arbor_fields[field](tree_nodes[i])

        return field_data

    def _get_header_fields(self, hfields, tree_nodes, dtypes):
        """
        Get fields from file header.
        """

        if not hfields:
            return {}

        field_data = {}
        hfield_values = dict((field, getattr(self, field))
                             for field in hfields)
        nt = len(tree_nodes)
        for field in hfields:
            field_data[field] = hfield_values[field] * \
              np.ones(nt, dtypes[field])

        return field_data

    def _read_data_default(self, rfields, dtypes):
        """
        Read field data for all halos in the file.
        """
        raise NotImplementedError

    def _read_data_select(self, rfields, tree_nodes, dtypes):
        """
        Read field data for a given set of halos.
        """
        raise NotImplementedError

    def _read_fields(self, fields, tree_nodes=None, dtypes=None):
        """
        Read all requested fields from disk, header, or arbor properties.
        """
        if dtypes is None:
            dtypes = {}

        field_data = {}
        afields, hfields, rfields = self._get_field_sources(fields)

        if tree_nodes is None:
            field_data = self._read_data_default(
                fields, dtypes)

        else:
            # fields from the actual data
            field_data.update(
                self._read_data_select(
                    rfields, tree_nodes, dtypes))

            # fields from arbor-related info
            field_data.update(
                self._get_arbor_fields(
                    afields, tree_nodes, dtypes))

            # fields from the file header
            field_data.update(
                self._get_header_fields(
                    hfields, tree_nodes, dtypes))

        return field_data
