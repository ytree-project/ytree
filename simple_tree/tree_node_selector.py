import numpy as np

from yt.utilities.operator_registry import \
    OperatorRegistry

tree_node_selector_registry = OperatorRegistry()

def add_tree_node_selector(name, function):
    tree_node_selector_registry[name] = TreeNodeSelector(function)

class TreeNodeSelector(object):
    r"""
    A TreeNodeSelector is responsible for choosing which one of a
    halo's ancestors to return for accessing fields from trees.

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
    return ancestors[np.argmin(vals)]

add_tree_node_selector("max_field_value", max_field_value)
