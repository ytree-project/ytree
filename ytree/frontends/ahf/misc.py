"""
AHFArbor miscellany



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
import os
import re

from ytree.utilities.io import f_text_block

def get_crm_filename(filename, suffix):
    # Searching for <keyword>.something.<suffix>
    res = re.search(f"([^\.]+)\.[^\.]+{suffix}$", filename)
    if not res:
        return None

    filekey = res.groups()[0]
    ddir = os.path.dirname(filekey)
    bname = os.path.basename(filekey)
    return os.path.join(ddir, f"MergerTree_{bname}.txt-CRMratio2")

def get_crm_table_value(f, index, table):
    if index in table:
        return table[index]

    indices = np.array(list(table.keys()))
    istart = min(indices[indices > index])
    if table[istart] is None:
        table[index] = None
        return table[index]

    f.seek(table[istart])
    current_cid = istart
    for line, loc in f_text_block(f):
        if line.startswith("END"):
            table[index] = None
            return table[index]
        online = line.split()
        thing = online[0]
        if len(online) == 2:
                cid = int(thing[:-12])
                if cid < current_cid:
                    table[cid] = loc
                    current_cid = cid
                    if cid == index:
                        return table[index]

def parse_AHF_file(filename, pars, sep=None):
    """
    Parse an AHF log or parameter file.
    """

    npars = len(pars.keys())
    vals = {}

    f = open(filename, "r")
    for line in f.readlines():
        line = line.strip()
        if line is None:
            break
        if len(vals.keys()) == npars:
            break
        for par in pars:
            key = pars[par]
            if key in vals:
                continue
            if line.startswith(f"{par} "):
                val = float(line.split(sep)[1])
                vals[key] = val
    f.close()

    if len(vals) < npars:
        mpars = ", ".join(set(pars.values()).difference(vals))
        raise RuntimeError(f"{filename} missing these parameters: {mpars}.")

    return vals
