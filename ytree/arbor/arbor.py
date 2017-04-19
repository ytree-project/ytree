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
import h5py
import glob
import numpy as np
import os
import warnings

from yt.convenience import \
    load as yt_load
from yt.extern.six import \
    add_metaclass, \
    string_types
from yt.frontends.ytdata.utilities import \
    save_as_dataset, \
    _hdf5_yt_array
from yt.funcs import \
    get_pbar, \
    get_output_filename
from yt.units.dimensions import \
    length
from yt.units.unit_registry import \
    UnitRegistry
from yt.units.yt_array import \
    UnitParseError, \
    YTArray, \
    YTQuantity
from yt.utilities.cosmology import \
    Cosmology

from ytree.arbor.tree_node import \
    TreeNode
from ytree.arbor.tree_node_selector import \
    tree_node_selector_registry
from ytree.utilities.io import \
    _hdf5_yt_attr
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
    def __init__(self, filename):
        """
        Initialize an Arbor given a single input file.
        """

        self.filename = filename
        self.basename = os.path.basename(filename)
        self.unit_registry = UnitRegistry()
        self._parse_parameter_file()
        self._set_default_selector()
        self._root_field_data = {}
        self._set_comoving_units()
        self.cosmology = Cosmology(
            hubble_constant=self.hubble_constant,
            omega_matter=self.omega_matter,
            omega_lambda=self.omega_lambda,
            unit_registry=self.unit_registry)

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

    def _set_comoving_units(self):
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

    def set_selector(self, selector, *args, **kwargs):
        r"""
        Sets the tree node selector to be used.

        This sets the manner in which halo ancestors are chosen
        from a list of ancestors when using the
        :func:`~ytee.tree_node.TreeNode._line` function to query fields
        for a tree.  The most obvious example is to always select
        the most massive ancestor so as to trace a halo's main
        progenitor.

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
        >>> a.set_selector("max_field_value", "mvir")

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
        Set the default tree node selector.

        Search for a mass-like field and use that with the
        max_field_value selector.
        """
        for field in ["particle_mass", "mvir"]:
            if field in self._field_data:
                self.set_selector("max_field_value", field)

    def _set_halo_id_field(self):
        """
        Figure out which field represents the halo IDs.
        """
        _hfields = ["halo_id", "particle_identifier"]
        hfields = [f for f in _hfields
                   if f in self._field_data]
        if len(hfields) == 0:
            raise RuntimeError("No halo id field found.")
        self._hid_field = hfields[0]

    def _get_root_fields(self, fields):
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

        fi = self.field_info
        field_data = {}
        for field in fields_to_read:
            units = self.field_info[field].get("units", "")
            field_data[field] = np.empty(self.trees.size)
            if units:
                field_data[field] = \
                  self.arr(field_data[field], units)
            for i in range(self.trees.size):
                field_data[field][i] = \
                  self.trees[i]._root_field_data[field]
        self._root_field_data.update(field_data)

    def _get_fields(self, tree_node, fields, root_only=True, f=None):
        """
        Load field data for a node or a tree into storage structures
        if not present.
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

        fields_to_read = []
        for field in fields:
            if field not in fcache:
                fields_to_read.append(field)

        if fields_to_read:
            field_data = self._read_fields(
                root_node, fields_to_read, root_only=root_only, f=f)
            self._store_fields(root_node, field_data, root_only)

    def _store_fields(self, root_node, field_data, root_only=False):
        if not field_data: return
        root_field_data = dict([(field, field_data[field][0])
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
                       "arbor_type": "ArborArbor",
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

class ArborArbor(MonolithArbor):
    """
    Class for Arbors created from the :func:`~ytree.arbor.Arbor.save_arbor`
    or :func:`~ytree.tree_node.TreeNode.save_tree` functions.
    """
    def _load_field_data(self):
        """
        All data stored in a single hdf5 file.  Get cosmological
        parameters and modify unit registry for hubble constant.
        """
        fh = h5py.File(self.filename, "r")
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            setattr(self, attr, fh.attrs[attr])
        if "unit_registry_json" in fh.attrs:
            self.unit_registry = \
              UnitRegistry.from_json(
                  fh.attrs["unit_registry_json"].astype(str))
        self.box_size = _hdf5_yt_attr(fh, "box_size",
                                      unit_registry=self.unit_registry)
        self._field_data = dict([(f, _hdf5_yt_array(fh["data"], f, self))
                                 for f in fh["data"]])
        fh.close()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have "arbor_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(".h5"): return False
        try:
            with h5py.File(fn, "r") as f:
                if "arbor_type" not in f.attrs:
                    return False
                if f.attrs["arbor_type"].astype(str) != "ArborArbor":
                    return False
        except:
            return False
        return True

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
