"""
io utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
from yt.units.yt_array import \
    YTArray, \
    YTQuantity

def parse_h5_attr(f, attr):
    """A Python3-safe function for getting hdf5 attributes.

    If an attribute is supposed to be a string, this will return it as such.

    This was taken from yt.
    """
    val = f.attrs.get(attr, None)
    if isinstance(val, bytes):
        return val.decode('utf8')
    else:
        return val

def _hdf5_yt_attr(fh, attr, unit_registry=None):
    """
    Read an hdf5 attribute.  If there exists another attribute
    named <attr>_units, use that to assign units and return
    as either a YTArray or YTQuantity.
    """
    val = fh.attrs[attr]
    units = ""
    ufield = "%s_units" % attr
    if ufield in fh.attrs:
        units = fh.attrs[ufield]
        if isinstance(units, bytes):
            units = units.decode("utf")
    if units == "dimensionless":
        units = ""
    if units != "":
        if isinstance(val, np.ndarray):
            val = YTArray(val, units, registry=unit_registry)
        else:
            val = YTQuantity(val, units, registry=unit_registry)
    return val

def _hdf5_yt_array_lite(fh, field):
    """
    Read an hdf5 dataset.  If that dataset has a "units" attribute,
    return that as well, but do not cast as a YTArray.
    """
    units = ""
    if "units" in fh[field].attrs:
        units = fh[field].attrs["units"]
    if units == "dimensionless": units = ""
    return (fh[field].value, units)
