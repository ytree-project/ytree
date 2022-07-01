"""
io utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import errno
import numpy as np
import os
from unyt import \
    unyt_array, \
    unyt_quantity

from yt.funcs import \
    get_pbar
from ytree.utilities.logger import \
    fake_pbar

def ensure_dir(path):
    r"""Parallel safe directory maker."""
    if os.path.exists(path):
        return path

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    return path

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
    as either a unyt_array or unyt_quantity.
    """
    val = fh.attrs[attr]
    units = ""
    ufield = f"{attr}_units"
    if ufield in fh.attrs:
        units = fh.attrs[ufield]
        if isinstance(units, bytes):
            units = units.decode("utf")
    if units == "dimensionless":
        units = ""
    if units != "":
        if isinstance(val, np.ndarray):
            val = unyt_array(val, units, registry=unit_registry)
        else:
            val = unyt_quantity(val, units, registry=unit_registry)
    return val

def _hdf5_yt_array_lite(fh, field):
    """
    Read an hdf5 dataset.  If that dataset has a "units" attribute,
    return that as well, but do not cast as a unyt_array.
    """
    units = ""
    if "units" in fh[field].attrs:
        units = fh[field].attrs["units"]
    if units == "dimensionless": units = ""
    return (fh[field][()], units)

def f_text_block(f, block_size=4096, file_size=None, sep="\n",
                 pbar_string=None):
    """
    Read lines from a file faster than f.readlines().
    """
    start = f.tell()
    if file_size is None:
        f.seek(0, 2)
        file_size = f.tell() - start
        f.seek(start)

    nblocks = np.ceil(float(file_size) /
                      block_size).astype(np.int64)
    read_size = file_size + start
    lbuff = ""
    if pbar_string is None:
        pbar = fake_pbar()
    else:
        pbar = get_pbar(pbar_string, file_size)
    for ib in range(nblocks):
        offset = f.tell()
        my_block = min(block_size, read_size-offset)
        if my_block <= 0: break
        buff = f.read(my_block)
        linl = -1
        for ih in range(buff.count(sep)):
            inl = buff.find(sep, linl+1)
            if inl < 0:
                lbuff += buff[linl+1:]
                continue
            else:
                line = lbuff + buff[linl+1:inl]
                loc = offset - len(lbuff) + linl + 1
                lbuff = ""
                linl = inl
                pbar.update(loc+len(line)-start+1)
                yield line, loc
        lbuff += buff[linl+1:]
    if lbuff:
        loc = f.tell() - len(lbuff)
        pbar.update(loc+len(lbuff)-start+1)
        yield lbuff, loc
    pbar.finish()
