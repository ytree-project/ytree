"""
HaloSelector functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from yt.funcs import \
    iterable
from yt.units.yt_array import \
    YTQuantity
from yt.utilities.operator_registry import \
    OperatorRegistry
from yt.utilities.exceptions import \
    YTSphereTooSmall

selector_registry = OperatorRegistry()

_id_cache = {}

def clear_id_cache():
    """
    Some HaloSelectors create a cache for quicker access.
    This clears that cache.
    """
    for key in _id_cache.keys():
        del _id_cache[key]

def add_halo_selector(name, function):
    r"""
    Add a HaloSelector to the registry of known selectors, so they
    can be chosen with `~ytree.tree_farm.TreeFarm.set_selector`.

    Parameters
    ----------
    name : string
        Name of the selector.
    function : callable
        The associated function.
    """
    selector_registry[name] = HaloSelector(function)

class HaloSelector(object):
    r"""
    A HaloSelector is a function that is responsible for creating a list
    of ids of halos that are potentially ancestors of a given halo.

    Required Arguments
    ------------------
    hc : halo container object
        Halo container associated with the target halo.
    ds2 : halo catalog-type dataset
        The dataset of the ancestor halos.

    The function should return a list of integers representing the ids
    of potential halos to check for ancestry.

    """
    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args
        if self.args is None: self.args = []
        self.kwargs = kwargs
        if self.kwargs is None: self.kwargs = {}

    def __call__(self, hc, ds2):
        return self.function(hc, ds2, *self.args, **self.kwargs)

def sphere_selector(hc, ds2, radius_field, factor=1,
                    min_radius=None):
    r"""
    Select halos within a sphere around the target halo.

    Parameters
    ----------
    hc : halo container object
        Halo container associated with the target halo.
    ds2 : halo catalog-type dataset
        The dataset of the ancestor halos.
    radius_field : str
        Name of the field to be used to get the halo radius.
    factor : float, optional
        Multiplicative factor of the halo radius in which
        potential halos will be gathered.  Default: 1.
    min_radius : YTQuantity or tuple of (value, unit)
        An absolute minimum radius for the sphere.

    Returns
    -------
    my_ids : list of ints
       List of ids of potential halos.

    """

    if min_radius is not None:
        if isinstance(min_radius, YTQuantity):
            pass
        elif iterable(min_radius) and len(min_radius) == 2:
            min_radius = ds2.quan(min_radius[0], min_radius[1])
        else:
            raise RuntimeError(
                "min_radius should be YTQuantity or (value, unit) tuple.")

    # Never mix code units from multiple datasets!!!
    center = ds2.arr(hc.position.to("code_length").d, "code_length")
    radius = factor * hc[radius_field]
    radius = ds2.quan(radius.to("code_length").d[0], "code_length")
    if min_radius is not None: radius = max(radius, min_radius)

    try:
        sp = ds2.sphere(center, radius)
        my_ids = sp[(hc.ptype, "particle_identifier")]
        my_ids = my_ids[np.argsort(sp[(hc.ptype, "particle_radius")])]
        return my_ids.d.astype(np.int64)
    except YTSphereTooSmall:
        return []

add_halo_selector("sphere", sphere_selector)

def all_selector(hc, ds2):
    r"""
    Return all halos from the ancestor dataset.

    Parameters
    ----------
    hc : halo container object
        Halo container associated with the target halo.
    ds2 : halo catalog-type dataset
        The dataset of the ancestor halos.

    Returns
    -------
    my_ids : list of ints
       List of ids of potential halos.

    """

    ad = ds2.all_data()
    if "all" in _id_cache:
        return _id_cache["all"]
    my_ids = ad[hc.ptype, "particle_identifier"].d.astype(np.int64)
    _id_cache["all"] = my_ids
    return my_ids

add_halo_selector("all", all_selector)
