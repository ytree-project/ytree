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
from yt.frontends.ytdata.utilities import \
    save_as_dataset
from yt.funcs import \
    get_output_filename

class TreeNode(object):
    """
    Class for objects stored in Arbors.

    Each TreeNode represents a halo in a tree.  A TreeNode knows
    its halo ID, the level in the tree, and its global ID in the
    Arbor that holds it.  It also has a list of its ancestors.
    Fields can be queried for it, its line, and the tree beneath.
    """
    def __init__(self, halo_id, level_id, global_id=None, arbor=None):
        """
        Initialize a TreeNode with at least its halo catalog ID and
        its level in the tree.
        """
        self.halo_id = halo_id
        self.level_id = level_id
        self.global_id = global_id
        self.ancestors = None
        self.arbor = arbor

    def add_ancestor(self, ancestor):
        """
        Add another TreeNode to the list of ancestors.

        Parameters
        ----------
        ancestor : TreeNode
            The ancestor TreeNode.
        """
        if self.ancestors is None:
            self.ancestors = []
        self.ancestors.append(ancestor)

    def __getitem__(self, field):
        """
        Return value of field for this TreeNode.
        """
        return self.arbor._field_data[field][self.global_id]

    def __repr__(self):
        return "TreeNode[%d,%d]" % (self.level_id, self.halo_id)

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
        tfi = []
        tn = []
        for my_node in self.twalk():
            tfi.append(my_node.global_id)
            tn.append(my_node)
        self._tfi = np.array(tfi)
        self._tn = tn

    _lfi = None
    @property
    def _line_field_indices(self):
        """
        Return the field array indices for all TreeNodes in
        the line, starting with this TreeNode.
        """
        if self._lfi is None:
            self._set_line_attrs()
        return self._lfi

    _ln = None
    @property
    def _line_nodes(self):
        """
        Return a list of all TreeNodes in the line, starting
        with this TreeNode.
        """
        if self._ln is None:
            self._set_line_attrs()
        return self._ln

    def _set_line_attrs(self):
        """
        Prepare the line list and field indices.
        """
        lfi = []
        ln = []
        for my_node in self.lwalk():
            lfi.append(my_node.global_id)
            ln.append(my_node)
        self._lfi = np.array(lfi)
        self._ln = ln

    def twalk(self):
        r"""
        An iterator over all TreeNodes in the tree beneath,
        starting with this TreeNode.

        Examples
        --------

        for my_node in my_tree.twalk():
            print (my_node)

        """
        yield self
        if self.ancestors is None:
            return
        for ancestor in self.ancestors:
            for a_node in ancestor.twalk():
                yield a_node

    def lwalk(self):
        r"""
        An iterator over all TreeNodes in the line,
        starting with this TreeNode.

        Examples
        --------

        for my_node in my_tree.lwalk():
            print (my_node)

        """
        my_node = self
        while my_node is not None:
            yield my_node
            if my_node.ancestors is None:
                my_node = None
            else:
                my_node = my_node.arbor.selector(my_node.ancestors)

    def tree(self, field):
        r"""
        Return a requested field for all TreeNodes in the tree
        beneath, starting with this TreeNode.

        Parameters
        ----------
        field : string
            The field to be queried.

        Examples
        --------
        print (my_tree.tree("mvir").to("Msun/h"))

        Returns
        -------
        ndarray or YTArray

        """
        if isinstance(field, string_types):
            return self.arbor._field_data[field][self._tree_field_indices]
        else:
            return self._tree_nodes[field]

    def line(self, field):
        r"""
        Return a requested field for all TreeNodes in the line,
        starting with this TreeNode.  By default, the line traces
        the most massive progenitor in the tree.

        Parameters
        ----------
        field : string
            The field to be queried.

        Examples
        --------
        print (my_tree.line("mvir").to("Msun/h"))

        Returns
        -------
        ndarray or YTArray

        """
        if isinstance(field, string_types):
            return self.arbor._field_data[field][self._line_field_indices]
        else:
            return self._line_nodes[field]

    def save_tree(self, filename=None, fields=None):
        r"""
        Save the tree to a file.

        The saved tree can be re-loaded as an arbor.

        Parameters
        ----------
        filename : optional, string
            Output filename.  Include a trailing "/" to indicate
            a directory.
            Default: "arbor_<level>_<halo_id>.h5"
        fields : optional, list of strings
            The fields to be saved.  If not given, all
            fields will be saved.

        Returns
        -------
        filename : string
            The filename of the saved arbor.

        """
        keyword = "tree_%d_%d" % (self.level_id, self.halo_id)
        filename = get_output_filename(filename, keyword, ".h5")
        if fields is None:
            fields = self.arbor._field_data.keys()
        ds = {}
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            if hasattr(self.arbor, attr):
                ds[attr] = getattr(self.arbor, attr)
        extra_attrs = {"box_size": self.arbor.box_size,
                       "arbor_type": "ArborArbor"}
        data = {}
        for field in fields:
            data[field] = self.tree(field)
        save_as_dataset(ds, filename, data,
                        extra_attrs=extra_attrs)
        return filename
