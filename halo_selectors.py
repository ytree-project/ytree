import numpy as np

from yt.utilities.operator_registry import \
    OperatorRegistry
from yt.utilities.exceptions import \
    YTSphereTooSmall

selector_registry = OperatorRegistry()

def add_selector(name, function):
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

def sphere_selector(hc, ds2, radius_field, factor=1):
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
    factor : float optional
        Multiplicative factor of the halo radius in which
        potential halos will be gathered.

    Returns
    -------
    my_ids : list of ints
       List of ids of potential halos.
    """

    radius = (factor * hc[radius_field]).in_units("code_length")
    try:
        sp = ds2.sphere(hc.position.in_units("code_length"), radius)
        my_ids = sp[(hc.ptype, "particle_identifier")]
        return my_ids.d.astype(np.int64)
    except YTSphereTooSmall:
        return []

add_selector("sphere", sphere_selector)
