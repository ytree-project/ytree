"""
AncestryFilter functions



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

ancestry_filter_registry = OperatorRegistry()

def add_ancestry_filter(name, function):
    ancestry_filter_registry[name] = AncestryFilter(function)

class AncestryFilter(object):
    r"""
    An AncestryFilter takes a halo and a list of ancestors and
    returns a filtered list of filtered list of ancestors.  For
    example, a filter could return only the most massive ancestor.

    Required Arguments
    ------------------
    halo: halo data container
        Data container of the descendent halo.
    ancestors : list of halo data containers
        List of data containers for the ancestor halos.

    The function should return a list of data containers.

    """
    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args
        if self.args is None: self.args = []
        self.kwargs = kwargs
        if self.kwargs is None: self.kwargs = {}

    def __call__(self, halo, ancestors):
        return self.function(halo, ancestors, *self.args, **self.kwargs)

def most_massive(halo, ancestors):
    r"""
    Return only the most massive ancestor.

    Parameters
    ----------
    halo: halo data container
        Data container of the descendent halo.
    ancestors : list of halo data containers
        List of data containers for the ancestor halos.

    Returns
    -------
    filtered_ancestors : list of halo data containers
        List containing data container of most massive halo.

    """
    if len(ancestors) == 0: return []
    i_max = np.argmax([my_halo.mass for my_halo in ancestors])
    return [ancestors[i_max]]

add_ancestry_filter("most_massive", most_massive)
