"""
TreeNode class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from yt.extern.six import \
    string_types

from ytree.arbor.fields import \
    FieldContainer

class TreeNode(object):
    """
    Class for objects stored in Arbors.

    Each TreeNode represents a halo in a tree.  A TreeNode knows
    its halo ID, the level in the tree, and its global ID in the
    Arbor that holds it.  It also has a list of its ancestors.
    Fields can be queried for it, its progenitor list, and the
    tree beneath.
    """
    def __init__(self, uid, arbor=None, root=False):
        """
        Initialize a TreeNode with at least its halo catalog ID and
        its level in the tree.
        """
        self.uid = uid
        self.arbor = arbor
        if root:
            self.root = -1
            self._root_field_data = FieldContainer(arbor)
            self._tree_field_data = FieldContainer(arbor)
        else:
            self.root = None

    @property
    def is_root(self):
        return self.root in [-1, self]

    def clear_fields(self):
        """
        If a root node, remove tree-related data structures.
        If not root node, do nothing.
        """

        if not self.is_root:
            return
        for attr in ["_root_field_data", "_tree_field_data"]:
            getattr(self, attr).clear()

    def add_ancestor(self, ancestor):
        """
        Add another TreeNode to the list of ancestors.

        Parameters
        ----------
        ancestor : TreeNode
            The ancestor TreeNode.
        """
        if self._ancestors is None:
            self._ancestors = []
        self._ancestors.append(ancestor)

    _ancestors = None
    @property
    def ancestors(self):
        if self.root == -1:
            self.arbor._grow_tree(self)
        return self._ancestors

    _uids = None
    @property
    def uids(self):
        if not self.is_root:
            return None
        if self._uids is None:
            self.arbor._setup_tree(self)
        return self._uids

    _descids = None
    @property
    def descids(self):
        if not self.is_root:
            return None
        if self._descids is None:
            self.arbor._setup_tree(self)
        return self._descids

    _tree_size = None
    @property
    def tree_size(self):
        if not self.is_root:
            return self["tree"].size
        if self._tree_size is None:
            self.arbor._setup_tree(self)
        return self._tree_size

    _nodes = None
    @property
    def nodes(self):
        if not self.is_root:
            return None
        self.arbor._grow_tree(self)
        return self._nodes

    def __setitem__(self, key, value):
        if self.root == -1:
            root = self
            treeid = 0
        else:
            root = self.root
            treeid = self.treeid
        self.arbor._node_io.get_fields(self, fields=[key],
                                       root_only=False)
        data = root._tree_field_data[key]
        data[treeid] = value

    def __getitem__(self, key):
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
        float, ndarray/YTArray, TreeNode

        """
        arr_types = ("prog", "tree")
        if isinstance(key, tuple):
            if len(key) != 2:
                raise SyntaxError(
                    "Must be either 1 or 2 arguments.")
            ftype, field = key
            if ftype == "line":
                raise SyntaxError(
                    "\"line\" has been deprecated. " +
                    "Please use \"prog\" instead.")
            if ftype not in arr_types:
                raise SyntaxError(
                    "First argument must be one of %s." % str(arr_types))
            self.arbor._setup_tree(self)
            self.arbor._node_io.get_fields(self, fields=[field], root_only=False)

            # field is an actual field
            if isinstance(field, string_types):
                indices = getattr(self, "_%s_field_indices" % ftype)
                return self.root._tree_field_data[field][indices]
            else:
                raise SyntaxError("Second argument must be a string.")

        else:
            if isinstance(key, string_types):
                # return the progenitor list or tree nodes in a list
                if key == "line":
                    raise SyntaxError(
                        "\"line\" has been deprecated. " +
                        "Please use \"prog\" instead.")
                if key in arr_types:
                    self.arbor._setup_tree(self)
                    return getattr(self, "_%s_nodes" % key)
                # return field value for this node
                self.arbor._node_io.get_fields(self, fields=[key])
                if self.is_root:
                    # temporary hack for analysis fields
                    if self.arbor.field_info[key].get("type") == "analysis":
                        return self._tree_field_data[key][0]
                    return self._root_field_data[key]
                else:
                    return self.root._tree_field_data[key][self.treeid]
            else:
                raise SyntaxError("Single argument must be a string.")

    def __repr__(self):
        return "TreeNode[%d]" % self.uid

    _tfi = None
    @property
    def _tree_field_indices(self):
        """
        Return the field array indices for all TreeNodes in
        the tree beneath, starting with this TreeNode.
        """
        if self._tfi is None:
            self._set_tree_attrs()
        return self._tfi

    _tn = None
    @property
    def _tree_nodes(self):
        """
        Return a list of all TreeNodes in the tree beneath,
        starting with this TreeNode.
        """
        if self._tn is None:
            self._set_tree_attrs()
        return self._tn

    def _set_tree_attrs(self):
        """
        Prepare the TreeNode list and field indices.
        """
        self.arbor._grow_tree(self)
        tfi = []
        tn = []
        for my_node in self.twalk():
            tfi.append(my_node.treeid)
            tn.append(my_node)
        self._tfi = np.array(tfi)
        self._tn = np.array(tn)

    _pfi = None
    @property
    def _prog_field_indices(self):
        """
        Return the field array indices for all TreeNodes in
        the progenitor list, starting with this TreeNode.
        """
        if self._pfi is None:
            self._set_prog_attrs()
        return self._pfi

    _pn = None
    @property
    def _prog_nodes(self):
        """
        Return a list of all TreeNodes in the progenitor list, starting
        with this TreeNode.
        """
        if self._pn is None:
            self._set_prog_attrs()
        return self._pn

    def _set_prog_attrs(self):
        """
        Prepare the progenitor list list and field indices.
        """
        self.arbor._grow_tree(self)
        lfi = []
        ln = []
        for my_node in self.pwalk():
            lfi.append(my_node.treeid)
            ln.append(my_node)
        self._pfi = np.array(lfi)
        self._pn = np.array(ln)

    def twalk(self):
        r"""
        An iterator over all TreeNodes in the tree beneath,
        starting with this TreeNode.

        Examples
        --------

        >>> for my_node in my_tree.twalk():
        ...     print (my_node)

        """
        self.arbor._grow_tree(self)
        yield self
        if self.ancestors is None:
            return
        for ancestor in self.ancestors:
            for a_node in ancestor.twalk():
                yield a_node

    def pwalk(self):
        r"""
        An iterator over all TreeNodes in the progenitor list,
        starting with this TreeNode.

        Examples
        --------

        >>> for my_node in my_tree.pwalk():
        ...     print (my_node)

        """
        self.arbor._grow_tree(self)
        my_node = self
        while my_node is not None:
            yield my_node
            if my_node.ancestors is None:
                my_node = None
            else:
                my_node = my_node.arbor.selector(my_node.ancestors)

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
