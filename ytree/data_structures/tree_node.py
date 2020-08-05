"""
TreeNode class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
import weakref

from ytree.data_structures.fields import \
    FieldContainer

class TreeNode:
    """
    Class for objects stored in Arbors.

    Each TreeNode represents a halo in a tree.  A TreeNode knows
    its halo ID, the level in the tree, and its global ID in the
    Arbor that holds it.  It also has a list of its ancestors.
    Fields can be queried for it, its progenitor list, and the
    tree beneath.
    """

    _link = None

    def __init__(self, uid, arbor=None, root=False):
        """
        Initialize a TreeNode with at least its halo catalog ID and
        its level in the tree.
        """
        self.uid = uid
        self.arbor = weakref.proxy(arbor)
        if root:
            self.root = -1
            self._field_data = FieldContainer(arbor)
        else:
            self.root = None

    _tree_id = None # used by CatalogArbor
    @property
    def tree_id(self):
        """
        Return the index of this node in a list of all nodes in the tree.
        """
        if self.is_root:
            return 0
        elif self._link is not None:
            return self._link.tree_id
        else:
            return self._tree_id

    @tree_id.setter
    def tree_id(self, value):
        """
        Set the tree_id manually in CatalogArbors.
        """
        self._tree_id = value

    @property
    def is_root(self):
        """
        Is this node the last in the tree?
        """
        return self.root in [-1, self]

    def find_root(self):
        """
        Find the root node.
        """

        if self.is_root:
            return self

        root = self.root
        if root is not None:
            return root

        return self.walk_to_root()

    def walk_to_root(self):
        """
        Walk descendents until root.
        """

        my_node = self
        while not my_node.is_root:
            if my_node.descendent in (-1, None):
                break
            my_node = my_node.descendent
        return my_node

    def clear_fields(self):
        """
        If a root node, delete field data.
        If not root node, do nothing.
        """

        if not self.is_root:
            return
        self._field_data.clear()

    _descendent = None # used by CatalogArbor
    @property
    def descendent(self):
        """
        Return the descendent node.
        """

        if self.is_root:
            return None

        # set in CatalogArbor._plant_trees
        if self._descendent is not None:
            return self._descendent

        # conventional Arbor object
        desc_link = self._link.descendent
        return self.arbor._generate_tree_node(self.root, desc_link)

    _ancestors = None # used by CatalogArbor
    @property
    def ancestors(self):
        """
        Return a generator of ancestor nodes.
        """

        self.arbor._grow_tree(self)

        # conventional Arbor object
        if self._link is not None:
            for link in self._link.ancestors:
                yield self.arbor._generate_tree_node(self.root, link)
            return

        # set in CatalogArbor._plant_trees
        if self._ancestors is not None:
            for ancestor in self._ancestors:
                yield ancestor
            return
        return None

    _uids = None
    @property
    def uids(self):
        """
        Array of uids for all nodes in the tree.
        """
        if not self.is_root:
            return None
        if self._uids is None:
            self.arbor._build_attr("_uids", self)
        return self._uids

    _desc_uids = None
    @property
    def desc_uids(self):
        """
        Array of descendent uids for all nodes in the tree.
        """
        if not self.is_root:
            return None
        if self._desc_uids is None:
            self.arbor._build_attr("_desc_uids", self)
        return self._desc_uids

    _tree_size = None
    @property
    def tree_size(self):
        """
        Number of nodes in the tree.
        """
        if self._tree_size is not None:
            return self._tree_size
        if self.is_root:
            self.arbor._setup_tree(self)
            # pass back to the arbor to avoid calculating again
            self.arbor._store_node_info(self, '_tree_size')
        else:
            self._tree_size = len(list(self["tree"]))
        return self._tree_size

    _link_storage = None
    @property
    def _links(self):
        """
        Array of NodeLink objects with the ancestor/descendent structure.

        This is only used by conventional Arbor objects, i.e., not
        CatalogArbor objects.
        """
        if not self.is_root:
            return None
        if self._link_storage is None:
            self.arbor._build_attr("_link_storage", self)
        return self._link_storage

    def __setitem__(self, key, value):
        """
        Set analysis field value for this node.
        """

        if self.is_root:
            root = self
            tree_id = 0
            # if root, set the value in the arbor field storage
            self.arbor._field_data[key][self._arbor_index] = value
        else:
            root = self.root
            tree_id = self.tree_id
        self.arbor._node_io.get_fields(self, fields=[key],
                                       root_only=False)
        data = root._field_data[key]
        data[tree_id] = value

    def __getitem__(self, key):
        """
        Return field values or tree/prog generators.
        """
        return self.query(key)

    def query(self, key):
        """
        Return field values for this TreeNode, progenitor list, or tree.

        Parameters
        ----------
        key : string or tuple
            If a single string, it can be either a field to be queried or
            one of "tree" or "prog".  If a field, then return the value of
            the field for this TreeNode.  If "tree" or "prog", then return
            the list of TreeNodes in the tree or progenitor list.

            If a tuple, this can be either (string, string) or (string, int),
            where the first argument must be either "tree" or "prog".
            If second argument is a string, then return the field values
            for either the tree or the progenitor list.  If second argument
            is an int, then return the nth TreeNode in the tree or progenitor
            list list.

        Examples
        --------
        >>> # virial mass for this halo
        >>> print (my_tree["mvir"].to("Msun/h"))

        >>> # all TreeNodes in the progenitor list
        >>> print (my_tree["prog"])
        >>> # all TreeNodes in the entire tree
        >>> print (my_tree["tree"])

        >>> # virial masses for the progenitor list
        >>> print (my_tree["prog", "mvir"].to("Msun/h"))

        >>> # the 3rd TreeNode in the progenitor list
        >>> print (my_tree["prog", 2])

        Returns
        -------
        float, ndarray/unyt_array, TreeNode

        """
        arr_types = ("prog", "tree")
        if isinstance(key, tuple):
            if len(key) != 2:
                raise SyntaxError(
                    "Must be either 1 or 2 arguments.")
            ftype, field = key
            if ftype not in arr_types:
                raise SyntaxError(
                    "First argument must be one of %s." % str(arr_types))
            if not isinstance(field, str):
                raise SyntaxError("Second argument must be a string.")

            self.arbor._node_io.get_fields(self, fields=[field], root_only=False)
            indices = getattr(self, "_%s_field_indices" % ftype)

            data_object = self.find_root()
            return data_object._field_data[field][indices]

        else:
            if not isinstance(key, str):
                raise SyntaxError("Single argument must be a string.")

            # return the progenitor list or tree nodes in a list
            if key in arr_types:
                self.arbor._setup_tree(self)
                return getattr(self, "_%s_nodes" % key)

            # return field value for this node
            self.arbor._node_io.get_fields(self, fields=[key],
                                           root_only=self.is_root)
            data_object = self.find_root()
            return data_object._field_data[key][self.tree_id]

    def __repr__(self):
        """
        Call me TreeNode.
        """
        return "TreeNode[%d]" % self.uid

    @property
    def _tree_nodes(self):
        """
        An iterator over all TreeNodes in the tree beneath,
        starting with this TreeNode.

        For internal use only. Use the following instead:

        >>> for my_node in my_tree['tree']:
        ...     print (my_node)

        Examples
        --------

        >>> for my_node in my_tree._tree_nodes:
        ...     print (my_node)

        """

        self.arbor._grow_tree(self)
        yield self
        if self.ancestors is None:
            return
        for ancestor in self.ancestors:
            for a_node in ancestor._tree_nodes:
                yield a_node

    _tfi = None
    @property
    def _tree_field_indices(self):
        """
        Return the field array indices for all TreeNodes in
        the tree beneath, starting with this TreeNode.
        """

        if self._tfi is not None:
            return self._tfi

        self.arbor._grow_tree(self)
        self._tfi = np.array([node.tree_id for node in self._tree_nodes])
        return self._tfi

    @property
    def _prog_nodes(self):
        """
        An iterator over all TreeNodes in the progenitor list,
        starting with this TreeNode.

        For internal use only. Use the following instead:

        >>> for my_node in my_tree['prog']:
        ...     print (my_node)

        Examples
        --------

        >>> for my_node in my_tree._prog_nodes:
        ...     print (my_node)

        """

        self.arbor._grow_tree(self)
        my_node = self
        while my_node is not None:
            yield my_node
            ancestors = [a for a in my_node.ancestors]
            if ancestors:
                my_node = my_node.arbor.selector(ancestors)
            else:
                my_node = None

    _pfi = None
    @property
    def _prog_field_indices(self):
        """
        Return the field array indices for all TreeNodes in
        the progenitor list, starting with this TreeNode.
        """

        if self._pfi is not None:
            return self._pfi

        self.arbor._grow_tree(self)
        self._pfi = np.array([node.tree_id for node in self._prog_nodes])
        return self._pfi

    def save_tree(self, filename=None, fields=None):
        r"""
        Save the tree to a file.

        The saved tree can be re-loaded as an arbor.

        Parameters
        ----------
        filename : optional, string
            Output file keyword.  Main header file will be named
            <filename>/<filename>.h5.
            Default: "tree_<uid>".
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
        >>> # save the first tree
        >>> fn = a[0].save_tree()
        >>> # reload it
        >>> a2 = ytree.load(fn)

        """

        if filename is None:
            filename = "tree_%d" % self.uid

        return self.arbor.save_arbor(
            filename=filename, fields=fields,
            trees=[self])
