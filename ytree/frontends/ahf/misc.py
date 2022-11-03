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
