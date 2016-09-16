"""
AncestryChecker functions



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

ancestry_checker_registry = OperatorRegistry()

def add_ancestry_checker(name, function):
    ancestry_checker_registry[name] = AncestryChecker(function)

class AncestryChecker(object):
    r"""
    An AncestryCheck is a function that is responsible for determining
    whether one halo is an ancestor of another.

    Required Arguments
    ------------------
    descendent_ids : list of ints
        Member ids for first halo.
    ancestor_ids : list of int
        Member ids for second halo.

    The function should return True or False.

    """
    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args
        if self.args is None: self.args = []
        self.kwargs = kwargs
        if self.kwargs is None: self.kwargs = {}

    def __call__(self, descendent_ids, ancestor_ids):
        return self.function(descendent_ids, ancestor_ids,
                             *self.args, **self.kwargs)

def common_ids(descendent_ids, ancestor_ids, threshold=0.5):
    r"""
    Determine if at least a given fraction of ancestor's member particles
    are in the descendent.

    Parameters
    ----------
    descendent_ids : list of ints
        Member ids for first halo.
    ancestor_ids : list of int
        Member ids for second halo.
    threshold : float, optional
        Critical fraction of ancestor's particles ending up in the
        descendent to be considered a true ancestor.  Default: 0.5.

    Returns
    -------
    True or False

    """

    common = np.intersect1d(descendent_ids, ancestor_ids)
    return common.size > threshold * ancestor_ids.size

add_ancestry_checker("common_ids", common_ids)
