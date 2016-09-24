"""
TreeNodeSelector functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
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
    can be chosen with `~ytree.arbor.Arbor.set_selector`.

    Parameters
    ----------
    name : string
        Name of the selector.
    function : callable
        The associated function.
    """
    tree_node_selector_registry[name] = TreeNodeSelector(function)

class TreeNodeSelector(object):
    r"""
    A TreeNodeSelector is responsible for choosing which one of a
    halo's ancestors to return for accessing fields from trees with
    the `~ytree.tree_node.TreeNode.line` function.

    Required Arguments
    ------------------
    ancestors : list of TreeNode objects
        List of TreeNode objects from which to select.

    The function should return a single TreeNode.

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
