"""
utilities



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

def mpi_gather_list(comm, my_list):
    my_list = comm.gather(my_list, root=0)
    rlist = []
    if comm.rank == 0:
        for my_item in my_list:
            rlist.extend(my_item)
    return rlist

def _hdf5_yt_attr(fh, attr, unit_registry=None):
    val = fh.attrs[attr]
    units = ""
    ufield = "%s_units" % attr
    if ufield in fh.attrs:
        units = fh.attrs[ufield]
    if units == "dimensionless":
        units = ""
    if units != "":
        if isinstance(val, np.ndarray):
            val = YTArray(val, units, registry=unit_registry)
        else:
            val = YTQuantity(val, units, registry=unit_registry)
    return val

def _hdf5_yt_array_lite(fh, field):
    units = ""
    if "units" in fh[field].attrs:
        units = fh[field].attrs["units"]
    if units == "dimensionless": units = ""
    return (fh[field].value, units)
