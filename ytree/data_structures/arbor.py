"""
Arbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
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
from unyt import \
    unyt_array, \
    unyt_quantity

from yt.funcs import \
    get_pbar, \
    TqdmProgressBar
from unyt.dimensions import \
    dimensionless, \
    length
from unyt.unit_registry import \
    UnitRegistry
from yt.utilities.cosmology import \
    Cosmology

from ytree.data_structures.fields import \
    FakeFieldContainer, \
    FieldContainer, \
    FieldInfoContainer
from ytree.data_structures.io import \
    DefaultRootFieldIO, \
    TreeFieldIO
from ytree.data_structures.node_link import \
    NodeLink
from ytree.data_structures.save_arbor import \
    save_arbor
from ytree.data_structures.tree_node import \
    TreeNode
from ytree.data_structures.tree_node_selector import \
    tree_node_selector_registry
from ytree.utilities.exceptions import \
    ArborFieldAlreadyExists, \
    ArborFieldDependencyNotFound
from ytree.utilities.logger import \
    fake_pbar, \
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

class Arbor(metaclass=RegisteredArbor):
    """
    Base class for all Arbor classes.

    Loads a merger-tree output file or a series of halo catalogs
    and create trees, stored in an array in
    :func:`~ytree.data_structures.arbor.Arbor.trees`.
    Arbors can be saved in a universal format with
    :func:`~ytree.data_structures.arbor.Arbor.save_arbor`. Also, provide some
    convenience functions for creating unyt_arrays and unyt_quantities and
    a cosmology calculator.
    """

    _field_info_class = FieldInfoContainer
    _root_field_io_class = DefaultRootFieldIO
    _tree_field_io_class = TreeFieldIO
    _default_dtype = np.float64

    ### attributes required for generating a TreeNode object
    ### for a given Arbor class.
    ### We store these in arrays and use them to generate TreeNodes
    ### when they are needed.
    ## attributes required for constructing TreeNodes
    _node_con_attrs = ('uid',)
    ## attributes we may not have, but would be nice if we did
    _node_too_attrs = ('_tree_size',)
    ## attributes specific to an Arbor class for facilitating io
    _node_io_attrs = ()

    ### tree node attributes for all Arbor types.
    ### These facilitate walking the tree, getting fields, etc.
    ### We keep track of these for resetting TreeNodes and
    ### deciding when they are setup or grown.
    _reset_attrs = ("_tfi", "_pfi")
    _setup_attrs = ("_desc_uids", "_uids")
    _grow_attrs = ("_link_storage", "_link")

    def __init__(self, filename):
        """
        Initialize an Arbor given an input file.
        """

        self.filename = filename
        self.basename = os.path.basename(filename)
        self.directory = os.path.dirname(filename)
        self._parse_parameter_file()
        self._set_units()
        self._setup_io()
        self._get_data_files()
        self._setup_fields()
        self._set_default_selector()

    def _parse_parameter_file(self):
        """
        Read relevant parameters from parameter file or file header
        and detect fields.
        """
        raise NotImplementedError

    def _set_units(self):
        """
        Set "cm" units for explicitly comoving.
        Note, we are using comoving units all the time since
        we are dealing with data at multiple redshifts.
        """
        for my_unit in ["m", "pc", "AU"]:
            new_unit = "%scm" % my_unit
            self._unit_registry.add(
                new_unit, self._unit_registry.lut[my_unit][0],
                length, self._unit_registry.lut[my_unit][3])

        self.cosmology = Cosmology(
            hubble_constant=self.hubble_constant,
            omega_matter=self.omega_matter,
            omega_lambda=self.omega_lambda,
            unit_registry=self.unit_registry)

    def _setup_io(self):
        """
        Create field io objects.
        """
        self._node_io = self._tree_field_io_class(
            self, default_dtype=self._default_dtype)
        self._root_io = self._root_field_io_class(
            self, default_dtype=self._default_dtype)

    def _get_data_files(self):
        """
        Get all files that hold field data and make them known
        to the i/o system.
        """
        pass

    def _setup_fields(self):
        """
        Setup field containers and definitions.
        """
        self._field_data = FieldContainer(self)
        self.derived_field_list = []
        self.analysis_field_list = []
        self.field_info.setup_known_fields()
        self.field_info.setup_aliases()
        self.field_info.setup_derived_fields()
        self.field_info.setup_vector_fields()

    def _set_default_selector(self):
        """
        Set the default tree node selector as maximum mass.
        """
        self.set_selector("max_field_value", "mass")

    @property
    def is_planted(self):
        """
        Determine if trees have been planted.
        """
        return self._node_info_storage is not None

    def _plant_trees(self):
        """
        Create arrays to construct root nodes.
        """
        raise NotImplementedError

    _node_info_storage = None
    @property
    def _node_info(self):
        """
        The dict of arrays for storing node information.
        """

        if self._node_info_storage is not None:
            return self._node_info_storage

        attrs = self._node_con_attrs + \
          self._node_io_attrs

        self._node_info_storage = \
          dict((attr, np.empty(self._size, dtype=np.int64))
               for attr in attrs)
        # initialize the target of opportunity attributes
        self._node_info_storage.update(
            dict((attr, -np.ones(self._size, dtype=np.int64))
                for attr in self._node_too_attrs))

        return self._node_info_storage

    def is_setup(self, tree_node):
        """
        Return True if arrays of uids and descendent uids have
        been read in. Setup has also completed if tree is already
        grown.
        """
        return self.is_grown(tree_node) or \
          tree_node._uids is not None

    def _setup_tree(self, tree_node, **kwargs):
        """
        Create arrays of uids and desc_uids and attach them to the
        root node.
        """

        # skip if this is not a root or if already setup
        if self.is_setup(tree_node):
            return

        idtype      = np.int64
        fields, _ = \
          self.field_info.resolve_field_dependencies(["uid", "desc_uid"])
        halo_id_f, desc_id_f = fields
        dtypes      = {halo_id_f: idtype, desc_id_f: idtype}
        field_data  = self._node_io._read_fields(tree_node, fields,
                                                 dtypes=dtypes, **kwargs)
        tree_node._uids      = field_data[halo_id_f]
        tree_node._desc_uids = field_data[desc_id_f]
        tree_node._tree_size = tree_node._uids.size

    def is_grown(self, tree_node):
        """
        Return True if a tree has been fully assembled, i.e.,
        the hierarchy of ancestor tree nodes has been built.
        """
        return tree_node.root != -1

    def _grow_tree(self, tree_node, **kwargs):
        """
        Construct the hierarchy of ancestors and descendents
        for all nodes in the tree.
        """

        # skip this if not a root or if already grown
        if self.is_grown(tree_node):
            return

        self._setup_tree(tree_node, **kwargs)
        size      = tree_node.tree_size
        uids      = tree_node.uids
        desc_uids = tree_node.desc_uids
        links     = np.empty(size, dtype=np.object)

        # Make a dict mapping uids to index of storage array.
        # First, try to get indices out as the dict is constructed
        # since the dict will be smaller at first.
        uidmap = {}
        not_found = []
        for i, (uid, desc_uid) in enumerate(zip(uids, desc_uids)):
            node = NodeLink(i)
            uidmap[uid] = i
            desc_index = uidmap.get(desc_uid)
            if desc_index is None:
                not_found.append((node, desc_uid))
            else:
                desc = links[desc_index]
                desc.add_ancestor(node)
            links[i] = node

        # Make any additional links missed on the first pass.
        for node, desc_uid in not_found:
            if desc_uid == -1:
                continue
            desc = links[uidmap[desc_uid]]
            desc.add_ancestor(node)

        tree_node.root = tree_node
        tree_node._link = links[0]
        tree_node._link_storage = links

    _attr_map = None
    def _build_attr(self, attr, tree_node):
        """
        Call the correct function for building a given attribute.
        """

        if self._attr_map is None:
            self._attr_map = \
              dict([(attr, self._setup_tree)
                    for attr in self._setup_attrs] +
                   [(attr, self._grow_tree)
                    for attr in self._grow_attrs])

        self._attr_map[attr](tree_node)

    def reset_node(self, tree_node):
        """
        Reset all data structures for a single node.

        The goal is to clear as many data structures as
        possible without rendering the node object useless,
        if they are intended to be kept around.

        Calling reset_node on a non-root node should not make
        the non-root node useless.

        Calling reset_node on a root node will render any
        generated non-root nodes useless.
        """

        tree_node.clear_fields()
        attrs = self._reset_attrs

        if tree_node.is_root:
            if self.is_grown(tree_node):
                attrs += self._grow_attrs
                tree_node.root = -1
            if self.is_setup(tree_node):
                attrs += self._setup_attrs

        for attr in attrs:
            setattr(tree_node, attr, None)

    def _node_io_loop(self, func, *args, **kwargs):
        """
        Call the provided function over a list of nodes.

        If possible, group nodes by common data files to speed
        things up.

        Parameters
        ----------
        func : function
            Function to be called on an array of nodes.
        pbar : optional, string or yt.funcs.TqdmProgressBar
            A progress bar to be updated with each iteration.
            If a string, a progress bar will be created and the
            finish function will be called. If a progress bar is
            provided, the finish function will not be called.
            Default: None (no progress bar).
        root_nodes : optional, array of root TreeNodes
            Array of nodes over which the function will be called.
            If None, the list will be self[:] (i.e., all
            root_nodes).
            Default: None.

        Returns
        -------
        rvals : list
            return values from calling func on each node.
            These will have the same order as the original node list.
        """

        pbar = kwargs.pop("pbar", None)
        root_nodes = kwargs.pop("root_nodes", None)

        data_files, node_list, return_order = \
          self._node_io_loop_prepare(root_nodes)
        nnodes = sum([nodes.size for nodes in node_list])

        finish = True
        if pbar is None:
            pbar = fake_pbar("", nnodes)
        elif not isinstance(pbar, TqdmProgressBar):
            pbar = get_pbar(pbar, nnodes)
        else:
            finish = False

        rvals = []
        for data_file, nodes in zip(data_files, node_list):
            self._node_io_loop_start(data_file)

            # if we're doing all of them, just give the indices
            if root_nodes is None:
                my_nodes = nodes
            else:
                my_nodes = root_nodes[nodes]

            for node in self._yield_root_nodes(my_nodes):
                rval = func(node, *args, **kwargs)
                rvals.append(rval)
                pbar.update(1)

            self._node_io_loop_finish(data_file)

        if finish:
            pbar.finish()

        if return_order is not None:
            rvals = [rvals[i] for i in return_order]

        return rvals

    def _node_io_loop_start(self, data_file):
        pass

    def _node_io_loop_finish(self, data_file):
        pass

    def _node_io_loop_prepare(self, nodes):
        """
        This is called at the beginning of _node_io_loop.

        In different frontends, this can be used to group nodes by
        common data files. If nodes is None, we want all root
        nodes in the Arbor.

        Below is the default behavior, which does the bare minimum
        of returning:
        list of [None] : meaning all nodes come in a single group
            associated with no particular data file.
        list containing array of all provided nodes: meaning there
            is no specific grouping to be done
        None : meaning the nodes do not have to be reordered after
            being processed.

        See the implementation in individual frontends for
        more informative examples.

        Returns
        -------
        data_files : list
            list of data files that will be used
        index_list : list of arrays
            indices of the provided array of nodes associated
            with each of the data files
        return_order : int array
            array of indices used to reorder the return values
            to the order of the provided nodes
        """

        self._plant_trees()

        if nodes is None:
            my_size = self.size
        else:
            my_size = nodes.size
        indices = np.arange(my_size)

        return [None], [indices], None

    def __iter__(self):
        """
        Iterate over all trees in the arbor.
        """

        self._plant_trees()
        for node in self._yield_root_nodes(range(self.size)):
            yield node

    def __repr__(self):
        return self.basename

    def __getitem__(self, key):
        return self.query(key)

    def query(self, key):
        """
        If given a string, return an array of field values for the
        roots of all trees.
        If given an integer, return a tree from the list of trees.
        """

        if isinstance(key, str):
            if key in ("tree", "prog"):
                raise SyntaxError("Argument must be a field or integer.")
            self._root_io.get_fields(self, fields=[key])
            return self._field_data[key]
        return self._generate_root_nodes(key)

    def _generate_root_nodes(self, key):
        """
        Create root nodes given an index or slice from uid array.
        """

        self._plant_trees()
        if isinstance(key, (int, np.integer)):
            return self._generate_root_node(key)
        elif isinstance(key, slice) or isinstance(key, np.ndarray):
            indices = np.arange(self.size)[key]
            return np.array(
                [node for node in self._yield_root_nodes(indices)])
        else:
            raise ValueError('Cannot generate nodes from argument: ', key)

    def _yield_root_nodes(self, indices):
        """
        Root node generator.
        """

        # If we've been given an array of TreeNodes,
        # just yield them back.
        if getattr(indices, 'dtype', None) == np.object:
            for index in indices:
                yield index
            return

        for index in indices:
            node = self._generate_root_node(index)
            yield node

    def _generate_root_node(self, index):
        """
        Create a root node given its index in the array of uids.
        """

        args = tuple(self._node_info[attr][index]
                      for attr in self._node_con_attrs)
        my_node = TreeNode(*args, arbor=self, root=True)
        my_node._arbor_index = index

        for attr in self._node_io_attrs:
            setattr(my_node, attr, self._node_info[attr][index])

        for attr in self._node_too_attrs:
            val = self._node_info[attr][index]
            if val != -1:
                setattr(my_node, attr, self._node_info[attr][index])

        return my_node

    def _generate_tree_node(self, root_node, node_link):
        """
        Create a non-root node in a tree.
        """

        tree_id = node_link.tree_id
        if tree_id == 0:
            return root_node
        uid        = root_node.uids[tree_id]
        node       = TreeNode(uid, arbor=self, root=False)
        node.root  = root_node
        node._link = node_link
        return node

    def _store_node_info(self, tree_node, attr):
        """
        Store a TreeNode attribute an array for retrieval later.
        """

        self._node_info[attr][tree_node._arbor_index] = \
          getattr(tree_node, attr)

    _field_info = None
    @property
    def field_info(self):
        """
        A dictionary containing information for each available field.
        """
        if self._field_info is None and \
          self._field_info_class is not None:
            self._field_info = self._field_info_class(self)
        return self._field_info

    _size = None
    @property
    def size(self):
        """
        Return total number of trees.
        """
        if self._size is None:
            self._plant_trees()
        return self._size

    def __len__(self):
        """
        Return total number of trees.
        """
        return self.size

    _unit_registry = None
    @property
    def unit_registry(self):
        """
        Unit system registry.
        """
        if self._unit_registry is None:
            self._unit_registry = UnitRegistry()
        return self._unit_registry

    @unit_registry.setter
    def unit_registry(self, value):
        self._unit_registry = value
        self._arr = None
        self._quan = None

    _hubble_constant = None
    @property
    def hubble_constant(self):
        """
        Value of the Hubble parameter.
        """
        return self._hubble_constant

    @hubble_constant.setter
    def hubble_constant(self, value):
        self._hubble_constant = value
        # reset the unit registry lut while preserving other changes
        self.unit_registry = UnitRegistry.from_json(
            self.unit_registry.to_json())
        if 'h' in self.unit_registry:
            self.unit_registry.modify("h", self.hubble_constant)
        else:
            self.unit_registry.add(
                'h', self.hubble_constant, dimensionless)

    _box_size = None
    @property
    def box_size(self):
        """
        The simulation box size.
        """
        return self._box_size

    @box_size.setter
    def box_size(self, value):
        self._box_size = value
        # set unitary as soon as we know the box size
        self.unit_registry.add(
            "unitary", float(self.box_size.in_base()), length)

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
        Create a unyt_array using the Arbor's unit registry.
        """
        if self._arr is not None:
            return self._arr
        self._arr = functools.partial(unyt_array,
                                      registry=self.unit_registry)
        return self._arr

    _quan = None
    @property
    def quan(self):
        """
        Create a unyt_quantity using the Arbor's unit registry.
        """
        if self._quan is not None:
            return self._quan
        self._quan = functools.partial(unyt_quantity,
                                       registry=self.unit_registry)
        return self._quan

    def select_halos(self, criteria, trees=None, select_from="tree",
                     fields=None):
        """
        Select halos from the arbor based on a set of criteria given as a string.


        Parameters
        ----------

        criteria: string
            A string that will eval to a Numpy-like selection operation
            performed on a TreeNode object called "tree".
            Example: 'tree["tree", "redshift"] > 1'
        trees : optional, list or array of TreeNodes
            A list or array of TreeNode objects in which to search. If none given,
            the search is performed over the full arbor.
        select_from : optional, "tree" or "prog"
            Determines whether to perform the search over the full tree or just
            the main progenitors. Note, the value given must be consistent with
            what appears in the criteria string. For example, a criteria
            string of 'tree["tree", "redshift"] > 1' cannot be used when setting
            select_from to "prog".
            Default: "tree".
        fields : optional, list of strings
            Use to provide a list of fields required by the criteria evaluation.
            If given, fields will be preloaded in an optimized way and the search
            will go faster.
            Default: None.

        Returns
        -------

        halos : array of TreeNodes
            A flat array of all TreeNodes meeting the criteria.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("tree_0_0_0.dat")
        >>> halos = a.select_halos('tree["tree", "redshift"] > 1',
        ...                        fields=["redshift"])
        >>>
        >>> halos = a.select_halos('tree["prog", "mass"].to("Msun") >= 1e10',
        ...                        select_from="prog", fields=["mass"])

        """

        if select_from not in ["tree", "prog"]:
            raise SyntaxError(
                "Keyword \"select_from\" must be either \"tree\" or \"prog\".")

        if trees is None:
            trees = self[:]

        if fields is None:
            fields = []

        self._node_io_loop(self._setup_tree, root_nodes=trees,
                           pbar="Setting up trees")
        if fields:
            self._node_io_loop(
                self._node_io.get_fields,
                pbar="Getting fields",
                root_nodes=trees, fields=fields, root_only=False)


        halos = []
        pbar = get_pbar("Selecting halos", trees.size)
        for tree in trees:
            my_filter = np.asarray(eval(criteria))
            select_group = np.asarray(list(tree[select_from]))
            if my_filter.size != select_group.size:
                raise RuntimeError(
                    ("Filter array and tree array sizes do not match. " +
                     "Make sure select_from (\"%s\") matches criteria (\"%s\").") %
                    (select_from, criteria))
            halos.extend(select_group[my_filter])
            pbar.update(1)
        pbar.finish()
        return np.array(halos)

    def add_analysis_field(self, name, units, dtype=None):
        r"""
        Add an empty field to be filled by analysis operations.

        Parameters
        ----------
        name : string
            Field name.
        units : string
            Field units.
        dtype : optional, type
            Data type for field values. If None, the default data type
            of the arbor is used.
            Default: None.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("tree_0_0_0.dat")
        >>> a.add_analysis_field("robots", "Msun * kpc")
        >>> # Set field for some halo.
        >>> a[0]["tree"][7]["robots"] = 1979.816
        """

        if name in self.field_info:
            raise ArborFieldAlreadyExists(name, arbor=self)

        if dtype is None:
            dtype = self._default_dtype

        self.analysis_field_list.append(name)
        self.field_info[name] = {"type": "analysis",
                                 "dtype": dtype,
                                 "units": units}
        self._field_data[name] = \
          self.arr(np.zeros(self.size, dtype=dtype), units)

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
            If True, add field even if it already exists and warn the
            user and raise an exception if dependencies do not exist.
            If False, silently do nothing in both instances.
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
            if force_add:
                raise ArborFieldDependencyNotFound(
                    field, alias, arbor=self)
            else:
                return

        if units is None:
            units = self.field_info[field].get("units")
        self.derived_field_list.append(alias)
        self.field_info[alias] = \
          {"type": "alias", "units": units,
           "dependencies": [field]}
        if "aliases" not in self.field_info[field]:
            self.field_info[field]["aliases"] = []
            self.field_info[field]["aliases"].append(alias)

    def add_derived_field(self, name, function,
                          units=None, dtype=None, description=None,
                          vector_field=False, force_add=True):
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
        dtype : optional, type
            The data type of the field array. If none, use the
            default type set by Arbor._default_dtype.
        description : optional, string
            A short description of the field.
        vector_field: optional, bool
            If True, field is an xyz vector.
            Default: False.
        force_add : optional, bool
            If True, add field even if it already exists and warn the
            user and raise an exception if dependencies do not exist.
            If False, silently do nothing in both instances.
            Default: True.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("tree_0_0_0.dat")
        >>> def _redshift(field, data):
        ...     return 1. / data["scale"] - 1
        ...
        >>> a.add_derived_field("redshift", _redshift)
        >>> print (a["redshift"])

        """

        if name in self.field_info:
            if force_add:
                ftype = self.field_info[name].get("type", "on-disk")
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
        if dtype is None:
            dtype = self._default_dtype
        info = {"name": name,
                "type": "derived",
                "function": function,
                "units": units,
                "dtype": dtype,
                "vector_field": vector_field,
                "description": description}

        fc = FakeFieldContainer(self, name=name)
        try:
            rv = function(info, fc)
        except TypeError as e:
            raise RuntimeError(
"""

Field function syntax in ytree has changed. Field functions must
now take two arguments, as in the following:
def my_field(field, data):
    return data['mass']

Check the TypeError exception above for more details.
""")
            raise e

        except ArborFieldDependencyNotFound as e:
            if force_add:
                raise e
            else:
                return

        rv.convert_to_units(units)
        info["dependencies"] = list(fc.keys())

        self.derived_field_list.append(name)
        self.field_info[name] = info

    @classmethod
    def _is_valid(cls, *args, **kwargs):
        """
        Check if input file works with a specific Arbor class.
        This is used with :func:`~ytree.data_structures.arbor.load` function.
        """
        return False

    def save_arbor(self, filename="arbor", fields=None, trees=None,
                   max_file_size=524288):
        r"""
        Save the arbor to a file.

        The saved arbor can be re-loaded as an arbor.

        Parameters
        ----------
        filename : optional, string
            Output file keyword.  If filename ends in ".h5",
            the main header file will be just that.  If not,
            filename will be <filename>/<basename>.h5.
            Default: "arbor".
        fields : optional, list of strings
            The fields to be saved.  If not given, all
            fields will be saved.
        trees : optional, list or array of TreeNodes
            If given, only save trees stemming from these nodes.
            If not provide, all trees will be saved.
        max_file_size : optional, float
            The maximum number of nodes saved to a single file.
            Smaller numbers will result in more files. Performance
            may change somewhat with different values.
            Default: 524288 (2^19).

        Returns
        -------
        header_filename : string
            The filename of the saved arbor.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("rockstar_halos/trees/tree_0_0_0.dat")
        >>> fn = a.save_arbor()
        >>> # reload it
        >>> a2 = ytree.load(fn)

        """

        fn = save_arbor(self, filename=filename,
                        fields=fields, trees=trees,
                        max_file_size=max_file_size)
        return fn

class CatalogArbor(Arbor):
    """
    Base class for Arbors created from a series of halo catalog
    files where the descendent ID for each halo has been
    pre-determined.

    Unlike formats where tree information is stored in single file,
    halos are scattered about multiple catalog files. This requires
    us to store the root TreeNode objects and their full assemblies.
    """

    _prefix = None
    _data_file_class = None
    # does the dataset define unique ids?
    _has_uids = False

    # We will store root TreeNodes instead of generate them,
    # so we don't need to store anything here.
    _node_con_attrs = ()

    # Don't reset _ancestors or descendents because we won't be able to
    # rebuild trees without calling _plant_trees again.
    _setup_attrs = ("_desc_uids", "_uids", "_nodes")
    _grow_attrs = ()

    def __init__(self, filename):
        super(CatalogArbor, self).__init__(filename)
        if not self._has_uids:
            if "uid" not in self.field_list:
                for field in "uid", "desc_uid":
                    self.field_list.append(field)
                    self.field_info[field] = {"units": "",
                                              "source": "arbor"}

    def _get_data_files(self):
        raise NotImplementedError

    def _generate_root_node(self, index):
        """
        Return a node self._trees.

        These cannot be generated easily, so we keep them.
        """
        node = self._trees[index]
        if not hasattr(node, '_arbor_index'):
            node._arbor_index = index
        return node

    _trees = None
    @property
    def is_planted(self):
        """
        Determine if trees have been planted.
        """
        return self._trees is not None

    def _plant_trees(self):
        """
        Construct all trees.

        Since nodes are spread out over multiple files, we will
        plant all trees and create all ancestor/descendent links.

        The links will be held by the nodes themselves and we will
        not store the nodes in an array until _setup_tree is called.
        """

        if self.is_planted:
            return

        # this can be called once with the list, but fields are
        # not guaranteed to be returned in order.
        if self._has_uids:
            id_fields = ["uid", "desc_uid"]
        else:
            id_fields = ["halo_id", "desc_id"]
        fields = \
          [self.field_info.resolve_field_dependencies([field])[0][0]
           for field in id_fields]
        halo_id_f, desc_id_f = fields
        dtypes = dict((field, np.int64) for field in fields)
        uid = 0
        trees = []
        nfiles = len(self.data_files)
        descs = lastids = None
        pbar = get_pbar("Planting trees", len(self.data_files))
        for i, dfl in enumerate(self.data_files):
            if not isinstance(dfl, list):
                dfl = [dfl]

            batches = []
            bsize = []
            hids = []
            ancs = defaultdict(list)
            for data_file in dfl:
                data = data_file._read_fields(fields, dtypes=dtypes)
                nhalos = len(data[halo_id_f])
                batch = np.empty(nhalos, dtype=object)

                for it in range(nhalos):
                    descid = data[desc_id_f][it]
                    if self._has_uids:
                        my_uid = data[halo_id_f][it]
                    else:
                        my_uid = uid
                    root = i == 0 or descid == -1
                    # The data says a descendent exists, but it's not there.
                    # This shouldn't happen, but it does sometimes.
                    if not root and descid not in lastids:
                        root = True
                        descid = data[desc_id_f][it] = -1
                    tree_node = TreeNode(my_uid, arbor=self, root=root)
                    tree_node._fi = it
                    tree_node.data_file = data_file
                    batch[it] = tree_node
                    if root:
                        trees.append(tree_node)
                    else:
                        ancs[descid].append(tree_node)
                    uid += 1
                data_file.trees = batch
                batches.append(batch)
                bsize.append(batch.size)
                hids.append(data[halo_id_f])

            if i > 0:
                for descid, ancestors in ancs.items():
                    # this will not be fast
                    descendent = descs[descid == lastids][0]
                    descendent._ancestors = ancestors
                    for ancestor in ancestors:
                        ancestor._descendent = descendent

            if i < nfiles - 1:
                descs = np.empty(sum(bsize), dtype=object)
                lastids = np.empty(descs.size, dtype=np.int64)
                ib = 0
                for batch, hid, bs in zip(batches, hids, bsize):
                    descs[ib:ib+bs] = batch
                    lastids[ib:ib+bs] = hid
                    ib += bs
            pbar.update(i)
        pbar.finish()

        self._trees = np.array(trees)
        self._size = self._trees.size

    def _setup_tree(self, tree_node):
        """
        Walk the tree and place all nodes into an array.

        This is required for field access.
        """

        if self.is_setup(tree_node):
            return

        nodes     = []
        uids      = []
        desc_uids = [-1]
        for i, node in enumerate(tree_node._tree_nodes):
            node._tree_id = i
            node.root     = tree_node
            nodes.append(node)
            uids.append(node.uid)
            if i > 0:
                desc_uids.append(node.descendent.uid)
        tree_node._nodes     = np.array(nodes)
        tree_node._uids      = np.array(uids)
        tree_node._desc_uids = np.array(desc_uids)
        tree_node._tree_size = tree_node._uids.size
        # This should bypass any attempt to get this field in
        # the conventional way.
        if self.field_info["uid"].get("source") == "arbor":
            tree_node._field_data["uid"] = tree_node._uids
            tree_node._field_data["desc_uid"] = tree_node._desc_uids

    def _grow_tree(self, tree_node):
        """
        Trees are grown when they are planted.
        """
        pass


global load_warn
load_warn = True

def load(filename, method=None, **kwargs):
    """
    Load an Arbor, determine the type automatically.

    Parameters
    ----------
    filename : string
        Input filename.
    method : optional, string
        The type of Arbor to be loaded.  Existing types are:
        ConsistentTrees, Rockstar, TreeFarm, YTree.  If not
        given, the type will be determined based on characteristics
        of the input file.
    kwargs : optional, dict
        Additional keyword arguments are passed to _is_valid and
        the determined type.

    Returns
    -------
    Arbor

    Examples
    --------

    >>> import ytree
    >>> # saved Arbor
    >>> a = ytree.load("arbor/arbor.h5")
    >>> # consistent-trees output
    >>> a = ytree.load("tiny_ctrees/locations.dat")
    >>> a = ytree.load("rockstar_halos/trees/tree_0_0_0.dat")
    >>> a = ytree.load("ctrees_hlists/hlists/hlist_0.12521.list")
    >>> # Rockstar catalogs
    >>> a = ytree.load("rockstar_halos/out_0.list")
    >>> # treefarm catalogs
    >>> a = ytree.load("my_halos/fof_subhalo_tab_025.0.h5")
    >>> # LHaloTree catalogs
    >>> a = ytree.load("my_halos/trees_063.0")
    >>> # Amiga Halo Finder
    >>> a = ytree.load("ahf_halos/snap_N64L16_000.parameter",
    ...                hubble_constant=0.7)

    """
    if not os.path.exists(filename):
        raise IOError("file does not exist: %s." % filename)
    if method is None:
        candidates = []
        for candidate, c in arbor_registry.items():
            if c._is_valid(filename, **kwargs):
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

    global load_warn
    if method not in ["YTree", "LHaloTree"] and load_warn:
        print(
            ("Performance will be improved by saving this arbor with " +
             "\"save_arbor\" and reloading:\n" +
             "\t>>> a = ytree.load(\"%s\")\n" +
             "\t>>> fn = a.save_arbor()\n" +
             "\t>>> a = ytree.load(fn)") % filename)
        load_warn = False
    return arbor_registry[method](filename, **kwargs)
