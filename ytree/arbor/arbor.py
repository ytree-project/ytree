"""
Arbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from collections import \
    defaultdict
import functools
import numpy as np
import os

from yt.extern.six import \
    add_metaclass, \
    string_types
from yt.frontends.ytdata.utilities import \
    save_as_dataset
from yt.funcs import \
    get_pbar, \
    get_output_filename, \
    just_one
from yt.units.dimensions import \
    length
from yt.units.unit_registry import \
    UnitRegistry
from yt.units.yt_array import \
    YTArray, \
    YTQuantity
from yt.utilities.cosmology import \
    Cosmology

from ytree.arbor.fields import \
    FakeFieldContainer, \
    FieldContainer
from ytree.arbor.tree_node import \
    TreeNode
from ytree.arbor.tree_node_selector import \
    tree_node_selector_registry
from ytree.utilities.exceptions import \
    ArborFieldCircularDependency, \
    ArborFieldNotFound
from ytree.utilities.logger import \
    ytreeLogger as mylog

arbor_registry = {}

class RegisteredArbor(type):
    """
    Add to the registry of known Arbor classes to cycle
    through in the load function.
    """
    def __init__(cls, name, b, d):
        type.__init__(cls, name, b, d)
        arbor_type = name[:name.rfind("Arbor")]
        if arbor_type:
            arbor_registry[arbor_type] = cls

@add_metaclass(RegisteredArbor)
class Arbor(object):
    """
    Base class for all Arbor classes.

    Loads a merger-tree output file or a series of halo catalogs
    and create trees, stored in an array in :func:`~ytree.arbor.Arbor.trees`.
    Arbors can be saved in a universal format with
    :func:`~ytree.arbor.Arbor.save_arbor`.  Also, provide some convenience
    functions for creating YTArrays and YTQuantities and a cosmology
    calculator.
    """

    _field_info_class = None

    def __init__(self, filename):
        """
        Initialize an Arbor given a single input file.
        """

        self.filename = filename
        self.basename = os.path.basename(filename)
        self.unit_registry = UnitRegistry()
        self._parse_parameter_file()
        self._set_units()
        self._root_field_data = FieldContainer(self)
        self._setup_fields()
        self._set_default_selector()

    def _plant_trees(self):
        pass

    def _grow_tree(self, **kwargs):
        pass

    def _grow_trees(self, root_nodes=None, **kwargs):
        if root_nodes is None:
            root_nodes = self.trees

        pbar = get_pbar("Growing trees", len(root_nodes))
        for node in root_nodes:
            self._grow_tree(node, **kwargs)
            pbar.update(1)
        pbar.finish()

    _trees = None
    @property
    def trees(self):
        if self._trees is None:
            self._plant_trees()
        return self._trees

    def __repr__(self):
        return self.basename

    def __getitem__(self, key):
        """
        If given a string, return an array of field values for the
        roots of all trees.
        If given an integer, return a tree from the list of trees.

        """
        if isinstance(key, string_types):
            if key in ("tree", "prog"):
                raise SyntaxError("Argument must be a field or integer.")
            self._get_root_fields([key])
            return self._root_field_data[key]
        return self.trees[key]

    def __iter__(self):
        """
        Iterate over all items in the tree list.
        """
        for t in self.trees:
            yield t

    def __len__(self):
        """
        Return length of tree list.
        """
        return self.trees.size

    _field_info = None
    @property
    def field_info(self):
        if self._field_info is None and \
          self._field_info_class is not None:
            self._field_info = self._field_info_class(self)
        return self._field_info

    @property
    def size(self):
        """
        Return length of tree list.
        """
        return self.trees.size

    _unit_registry = None
    @property
    def unit_registry(self):
        return self._unit_registry

    @unit_registry.setter
    def unit_registry(self, value):
        self._unit_registry = value
        self._arr = None
        self._quan = None

    _hubble_constant = None
    @property
    def hubble_constant(self):
        return self._hubble_constant

    @hubble_constant.setter
    def hubble_constant(self, value):
        self._hubble_constant = value
        # reset the unit registry lut while preserving other changes
        self.unit_registry = UnitRegistry.from_json(
            self.unit_registry.to_json())
        self.unit_registry.modify("h", self.hubble_constant)

    _box_size = None
    @property
    def box_size(self):
        return self._box_size

    @box_size.setter
    def box_size(self, value):
        self._box_size = value
        # set unitary as soon as we know the box size
        self.unit_registry.add(
            "unitary", float(self.box_size.in_base()), length)

    def _setup_fields(self):
        self.derived_field_list = []
        self.field_info.setup_aliases()
        self.field_info.setup_derived_fields()

    def _set_units(self):
        """
        Set "cm" units for explicitly comoving.
        Note, we are using comoving units all the time since
        we are dealing with data at multiple redshifts.
        """
        for my_unit in ["m", "pc", "AU", "au"]:
            new_unit = "%scm" % my_unit
            self._unit_registry.add(
                new_unit, self._unit_registry.lut[my_unit][0],
                length, self._unit_registry.lut[my_unit][3])

        self.cosmology = Cosmology(
            hubble_constant=self.hubble_constant,
            omega_matter=self.omega_matter,
            omega_lambda=self.omega_lambda,
            unit_registry=self.unit_registry)

    def set_selector(self, selector, *args, **kwargs):
        r"""
        Sets the tree node selector to be used.

        This sets the manner in which halo progenitors are
        chosen from a list of ancestors.  The most obvious example
        is to select the most massive ancestor.

        Parameters
        ----------
        selector : string
            Name of the selector to be used.

        Any additional arguments and keywords to be provided to
        the selector function should follow.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("rockstar_halos/trees/tree_0_0_0.dat")
        >>> a.set_selector("max_field_value", "mass")

        """
        self.selector = tree_node_selector_registry.find(
            selector, *args, **kwargs)

    _arr = None
    @property
    def arr(self):
        """
        Create a YTArray using the Arbor's unit registry.
        """
        if self._arr is not None:
            return self._arr
        self._arr = functools.partial(YTArray,
                                      registry=self.unit_registry)
        return self._arr

    _quan = None
    @property
    def quan(self):
        """
        Create a YTQuantity using the Arbor's unit registry.
        """
        if self._quan is not None:
            return self._quan
        self._quan = functools.partial(YTQuantity,
                                       registry=self.unit_registry)
        return self._quan

    def _set_default_selector(self):
        """
        Set the default tree node selector as maximum mass.
        """
        self.set_selector("max_field_value", "mass")

    def add_alias_field(self, alias, field, units=None,
                        force_add=True):
        r"""
        Add a field as an alias to another field.

        Parameters
        ----------
        alias : string
            Alias name.
        field : string
            The field to be aliased.
        units : optional, string
            Units in which the field will be returned.
        force_add : optional, bool
            If True, add field even if it already exists
            and warn the user.  If False, silently do
            nothing.
            Default: True.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("tree_0_0_0.dat")
        >>> # "Mvir" exists on disk
        >>> a.add_alias_field("mass", "Mvir", units="Msun")
        >>> print (a["mass"])

        """

        if alias in self.field_info:
            if force_add:
                ftype = self.field_info[alias].get("type", "on-disk")
                if ftype in ["alias", "derived"]:
                    fl = self.derived_field_list
                else:
                    fl = self.field_list
                mylog.warn(
                    ("Overriding field \"%s\" that already " +
                     "exists as %s field.") % (alias, ftype))
                fl.pop(fl.index(alias))
            else:
                return

        if field not in self.field_info:
            raise RuntimeError(
                "Field not available: %s (dependency for %s)." %
                (field, alias))
        if units is None:
            units = self.field_info[field].get("units")
        self.derived_field_list.append(alias)
        self.field_info[alias] = \
          {"type": "alias", "units": units,
           "dependencies": [field]}

    def add_derived_field(self, name, function,
                          units=None, description=None,
                          force_add=True):
        r"""
        Add a field that is a function of other fields.

        Parameters
        ----------
        name : string
            Field name.
        function : callable
            The function to be called to generate the field.
            This function should take two arguments, the
            arbor and the data structure containing the
            dependent fields.  See below for an example.
        units : optional, string
            The units in which the field will be returned.
        description : optional, string
            A short description of the field.
        force_add : optional, bool
            If True, add field even if it already exists
            and warn the user.  If False, silently do
            nothing.
            Default: True.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("tree_0_0_0.dat")
        >>> def _redshift(arbor, data):
        ...     return 1. / data["scale"] - 1
        ...
        >>> a.add_derived_field("redshift", _redshift)
        >>> print (a["redshift"])

        """

        if name in self.field_info:
            if force_add:
                ftype = self.field_info[name].get("type", "on-disk")
                print (ftype)
                if ftype in ["alias", "derived"]:
                    fl = self.derived_field_list
                else:
                    fl = self.field_list
                mylog.warn(
                    ("Overriding field \"%s\" that already " +
                     "exists as %s field.") % (name, ftype))
                fl.pop(fl.index(name))
            else:
                return

        if units is None:
            units = ""
        fc = FakeFieldContainer(self, name=name)
        rv = function(fc)
        rv.convert_to_units(units)
        self.derived_field_list.append(name)
        self.field_info[name] = \
          {"type": "derived", "function": function,
           "units": units, "description": description,
           "dependencies": list(fc.keys())}

    def _get_root_fields(self, fields):
        """
        Get fields for the root nodes of all trees.
        """
        fields_to_read = []
        for field in fields:
            if field not in self._root_field_data:
                fields_to_read.append(field)
        if not fields_to_read:
            return

        f = open(self.filename, "r")
        for node in self.trees:
            self._get_fields(node, fields_to_read,
                             root_only=True, f=f)
        f.close()

        field_data = {}
        fi = self.field_info
        for field in fields_to_read:
            units = fi[field].get("units", "")
            field_data[field] = np.empty(self.trees.size)
            if units:
                field_data[field] = \
                  self.arr(field_data[field], units)
            for i in range(self.trees.size):
                field_data[field][i] = \
                  self.trees[i]._root_field_data[field]
        self._root_field_data.update(field_data)

    def _get_fields(self, tree_node, fields, root_only=True, f=None):
        r"""
        Load field data for a node or a tree into storage structures.

        This is the primary function for generating fields.
        Resolve dependencies, read in any fields needed from disk,
        then generate all derived fields.

        Parameters
        ----------
        tree_node : TreeNode
            Tree for which the fields will be generated.
        fields : list of strings
            The list of fields to be generated.
        root_only : optional, bool
            If True, only read/generate field for the root node
            in the tree.  If False, generate for the whole tree.
            Default: True.
        f : optional, file
            If not None, read data from the open file and do not
            close.  If None, open the file and close after reading.
            This can be used to speed up reading for multiple trees.

        """
        if tree_node.root == -1:
            root_node = tree_node
        else:
            root_node = tree_node.root
            root_only = False

        if root_only:
            fcache = root_node._root_field_data
        else:
            fcache = root_node._tree_field_data

        fi = self.field_info

        # Resolve field dependencies.
        fields_to_read, fields_to_generate = \
          self._resolve_field_dependencies(fields, fcache=fcache)

        # Read in fields we need that are on disk.
        if fields_to_read:
            field_data = self._read_fields(
                root_node, fields_to_read, root_only=root_only, f=f)
            self._store_fields(root_node, field_data,
                               root_only=root_only)

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
                self._store_fields(root_node, fdata,
                                   root_only=root_only)

    def _resolve_field_dependencies(self, fields, fcache=None):
        """
        Divide fields into those to be read and those to generate.
        """
        if fcache is None:
            fcache = {}
        fi = self.field_info
        fields_to_read = []
        fields_to_generate = []
        fields_to_resolve = fields.copy()

        while len(fields_to_resolve) > 0:
            field = fields_to_resolve.pop(0)
            if field in fcache:
                continue
            if field not in fi:
                raise ArborFieldNotFound(field, self)
            ftype = fi[field].get("type")
            if ftype == "derived" or ftype == "alias":
                deps = fi[field]["dependencies"]
                if field in deps:
                    raise ArborFieldCircularDependency(field, self)
                fields_to_resolve.extend(
                    set(deps).difference(set(fields_to_resolve)))
                if field not in fields_to_generate:
                    fields_to_generate.append(field)
            else:
                if field not in fields_to_read:
                    fields_to_read.append(field)
        return fields_to_read, fields_to_generate

    def _store_fields(self, root_node, field_data, root_only=False):
        """
        Store field data in the provided dictionary.
        """
        if not field_data: return
        root_field_data = dict(
            [(field, just_one(field_data[field]))
             for field in field_data])
        if not root_only:
            root_node._tree_field_data.update(field_data)
        root_node._root_field_data.update(root_field_data)

    @classmethod
    def _is_valid(cls, *args, **kwargs):
        """
        Check if input file works with a specific Arbor class.
        This is used with :func:`~ytree.arbor.load` function.
        """
        return False

    def save_arbor(self, filename=None, fields=None):
        r"""
        Save the arbor to a file.

        The saved arbor can be re-loaded as an arbor.

        Parameters
        ----------
        filename : optional, string
            Output filename.  Include a trailing "/" to indicate
            a directory.
            Default: "arbor.h5"
        fields : optional, list of strings
            The fields to be saved.  If not given, all
            fields will be saved.

        Returns
        -------
        filename : string
            The filename of the saved arbor.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("rockstar_halos/trees/tree_0_0_0.dat")
        >>> fn = a.save_arbor()
        >>> # reload it
        >>> a2 = ytree.load(fn)

        """
        filename = get_output_filename(filename, "arbor", ".h5")
        if fields is None:
            fields = self.field_list
        ds = {}
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            if hasattr(self, attr):
                ds[attr] = getattr(self, attr)
        extra_attrs = {"box_size": self.box_size,
                       "arbor_type": "YTreeArbor",
                       "unit_registry_json": self.unit_registry.to_json()}
        save_as_dataset(ds, filename, self._field_data,
                        extra_attrs=extra_attrs)
        return filename

class MonolithArbor(Arbor):
    """
    Base class for Arbors loaded from a single file.
    """
    def _load_field_data(self):
        """
        Load all fields from file, store in self._field_data.
        """
        pass

    def _load_trees(self):
        """
        Create the tree structure.
        """
        self._load_field_data()
        self._set_halo_id_field()

        self._trees = []
        root_ids = self._field_data["uid"][self._field_data["desc_id"] == -1]
        if hasattr(root_ids, "units"):
            root_ids = root_ids.d
        root_ids = root_ids.astype(np.int64, copy=False)
        pbar = get_pbar("Loading %d trees" % root_ids.size,
                        self._field_data["uid"].size)
        for root_id in root_ids:
            tree_halos = (root_id == self._field_data["tree_id"])
            my_tree = {}
            for i in np.where(tree_halos)[0]:
                desc_id = np.int64(self._field_data["desc_id"][i])
                uid = np.int64(self._field_data["uid"][i])
                my_node = TreeNode(i, arbor=self)
                my_tree[uid] = my_node
                if desc_id >= 0:
                    my_tree[desc_id].add_ancestor(my_node)
                pbar.update(1)
            self._trees.append(my_tree[root_id])
        pbar.finish()
        self._trees = np.array(self._trees)
        mylog.info("Arbor contains %d trees with %d total nodes." %
                   (self._trees.size, self._field_data["uid"].size))

class CatalogArbor(Arbor):
    """
    Base class for Arbors created from a series of halo catalog
    files where the descendent ID for each halo has been
    pre-determined.
    """
    def _get_all_files(self):
        """
        Get all input files based on specific naming convention.
        """
        pass

    def _load_field_data(self, *args):
        """
        Load field data from a single halo catalog.
        """
        pass

    def _to_field_array(self, field, data):
        """
        Determines how final field arrays are defined, assigns
        units if they have been pre-defined.
        """
        if len(data) == 0:
            return np.array(data)
        if isinstance(data[0], YTArray):
            # Override the dataset's units with the arbor's
            # to avoid lingering comoving/proper definitions.
            self._field_data[field] = \
              self.arr(data, str(data[0].units))
        else:
            self._field_data[field] = np.array(data)

    def _load_trees(self):
        """
        Create the tree structure from the input files.
        """
        my_files = self._get_all_files()
        self._field_data = defaultdict(list)

        offset = 0
        anc_ids = None
        anc_nodes = None
        my_trees = []
        pbar = get_pbar("Load halo catalogs", len(my_files))
        for i, fn in enumerate(my_files):
            n_halos = self._load_field_data(fn, offset)
            if n_halos == 0:
                pbar.update(i)
                continue

            my_nodes = []
            for halo in range(n_halos):
                my_node = TreeNode(self._field_data["uid"][-1][halo],
                                   arbor=self)
                my_nodes.append(my_node)
                if self._field_data["desc_id"][-1][halo] == -1 or i == 0:
                    my_trees.append(my_node)

            if anc_ids is not None:
                des_ids = anc_ids
                des_nodes = anc_nodes
            anc_ids = self._field_data["halo_id"][-1]
            anc_nodes = my_nodes

            offset += n_halos
            if i == 0:
                pbar.update(i)
                continue

            for halo in range(n_halos):
                des_id = self._field_data["desc_id"][-1][halo]
                if des_id == -1: continue
                i_des = np.where(des_id == des_ids)[0][0]
                des_nodes[i_des].add_ancestor(anc_nodes[halo])

            pbar.update(i)
        pbar.finish()
        self._trees = np.array(my_trees)

        for field in self._field_data:
            my_data = []
            for level in self._field_data[field]:
                my_data.extend(level)
            self._to_field_array(field, my_data)

        self._field_data["tree_id"] = -np.ones(offset)
        for t in self._trees:
            self._field_data["tree_id"][t._tree_field_indices] = t["uid"]
            for tnode in t.twalk():
                if tnode.ancestors is None: continue
                for a in tnode.ancestors:
                    self._field_data["desc_id"][a.uid] = tnode["uid"]
        assert (self._field_data["tree_id"] != -1).any()

        mylog.info("Arbor contains %d trees with %d total nodes." %
                   (self._trees.size, offset))

def load(filename, method=None):
    """
    Load an Arbor, determine the type automatically.

    Parameters
    ----------
    filename : string
        Input filename.
    method : optional, string
        The type of Arbor to be loaded.  Existing types are:
        Arbor, ConsistentTrees, Rockstar, TreeFar.  If not
        given, the type will be determined based on characteristics
        of the input file.

    Returns
    -------
    Arbor

    Examples
    --------

    >>> import ytree
    >>> # saved Arbor
    >>> a = ytree.load("arbor.h5")
    >>> # consistent-trees output
    >>> a = ytree.load("rockstar_halos/trees/tree_0_0_0.dat")
    >>> # Rockstar catalogs
    >>> a = ytree.load("rockstar_halos/out_0.list")
    >>> # TreeFarm catalogs
    >>> a = ytree.load("my_halos/fof_subhalo_tab_025.0.hdf5.0.h5")

    """
    if not os.path.exists(filename):
        raise IOError("file does not exist: %s." % filename)
    if method is None:
        candidates = []
        for candidate, c in arbor_registry.items():
            if c._is_valid(filename):
                candidates.append(candidate)
        if len(candidates) == 0:
            raise IOError("Could not determine arbor type for %s." % filename)
        elif len(candidates) > 1:
            errmsg = "Could not distinguish between these arbor types:\n"
            for candidate in candidates:
                errmsg += "Possible: %s.\n" % candidate
            errmsg += "Provide one of these types using the \'method\' keyword."
            raise IOError(errmsg)
        else:
            method = candidates[0]
    else:
        if method not in arbor_registry:
            raise IOError("Invalid method: %s.  Available: %s." %
                          (method, arbor_registry.keys()))
    return arbor_registry[method](filename)
