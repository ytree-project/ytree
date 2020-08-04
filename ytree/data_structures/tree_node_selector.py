"""
TreeNodeSelector functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from yt.utilities.operator_registry import \
    OperatorRegistry

tree_node_selector_registry = OperatorRegistry()

def add_tree_node_selector(name, function):
    r"""
    Add a TreeNodeSelector to the registry of known selectors, so they
    can be chosen with :func:`~ytree.data_structures.arbor.Arbor.set_selector`.

    Parameters
    ----------
    name : string
        Name of the selector.
    function : callable
        The associated function.

    Examples
    --------

    >>> import ytree
    >>> def max_value(ancestors, field):
    ...     vals = np.array([a[field] for a in ancestors])
    ...     return ancestors[np.argmax(vals)]
    >>> ytree.add_tree_node_selector("max_field_value", max_value)
    >>> a = ytree.load("tree_0_0_0.dat")
    >>> a.set_selector("max_field_value", "mass")
    >>> print (a[0]["prog"])

    """
    tree_node_selector_registry[name] = TreeNodeSelector(function)

class TreeNodeSelector:
    r"""
    The TreeNodeSelector is responsible for choosing which one of a
    halo's ancestors to return when querying the line of main
    progenitors for a halo.

    Parameters
    ----------
    ancestors : list of TreeNode objects
        List of TreeNode objects from which to select.

    The function should return a single TreeNode.

    Examples
    --------

    >>> import ytree
    >>> def max_value(ancestors, field):
    ...     vals = np.array([a[field] for a in ancestors])
    ...     return ancestors[np.argmax(vals)]
    >>> ytree.add_tree_node_selector("max_field_value", max_value)
    >>> a = ytree.load("tree_0_0_0.dat")
    >>> a.set_selector("max_field_value", "mass")
    >>> print (a[0]["prog"])

    """
    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args
        if self.args is None: self.args = []
        self.kwargs = kwargs
        if self.kwargs is None: self.kwargs = {}

    def __call__(self, ancestors):
        return self.function(ancestors, *self.args, **self.kwargs)

def max_field_value(ancestors, field):
    r"""
    Return the TreeNode with the maximum value of the given field.

    Parameters
    ----------
    ancestors : list of TreeNode objects
        List of TreeNode objects from which to select.
    field : string
        Field to be used for selection.

    Returns
    -------
    TreeNode object

    """

    vals = np.array([a[field] for a in ancestors])
    return ancestors[np.argmax(vals)]


add_tree_node_selector("max_field_value", max_field_value)

def min_field_value(ancestors, field):
    r"""
    Return the TreeNode with the minimum value of the given field.

    Parameters
    ----------
    ancestors : list of TreeNode objects
        List of TreeNode objects from which to select.
    field : string
        Field to be used for selection.

    Returns
    -------
    TreeNode object

    """

    vals = np.array([a[field] for a in ancestors])
    return ancestors[np.argmin(vals)]


add_tree_node_selector("min_field_value", min_field_value)
