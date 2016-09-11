"""
AncestryShort functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from yt.utilities.operator_registry import \
    OperatorRegistry

ancestry_short_registry = OperatorRegistry()

def add_ancestry_short(name, function):
    ancestry_short_registry[name] = AncestryShort(function)

class AncestryShort(object):
    r"""
    An AncestryShort takes a halo and an ancestor halo and
    determines if the ancestry search should come to an end.

    Required Arguments
    ------------------
    halo: halo data container
        Data container of the descendent halo.
    ancestor : halo data container
        Data container for the ancestor halo.

    The function should return True or False.

    """
    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args
        if self.args is None: self.args = []
        self.kwargs = kwargs
        if self.kwargs is None: self.kwargs = {}

    def __call__(self, halo, ancestor):
        return self.function(halo, ancestor, *self.args, **self.kwargs)

def above_mass_fraction(halo, ancestor, fraction):
    r"""
    Return only the most massive ancestor.

    Parameters
    ----------
    halo: halo data container
        Data container of the descendent halo.
    ancestor : halo data container
        Data containers for the ancestor halo.

    Returns
    -------
    True or False

    """
    return ancestor.mass > fraction * halo.mass

add_ancestry_short("above_mass_fraction", above_mass_fraction)
