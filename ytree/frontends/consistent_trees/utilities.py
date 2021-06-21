"""
ConsistentTreesArbor utility functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import re

from unyt.exceptions import \
    UnitParseError

def parse_ctrees_header(arbor, input_stream,
                        ntrees_in_file=True):
    """
    Parse consistent-trees header information.

    Parse ascii text from a file or list of strings to get:
    - cosmology parameters
    - box size
    - fields and units
    - optionally, number of trees and end of header file offset

    Return a dictionary of field information.
    """
    fields = []
    fi = {}
    fdb = {}
    rems = [f"{s[0]}{t}{s[1]}"
            for s in [("(", ")"), ("", "")]
            for t in ["physical, peculiar",
                      "comoving", "physical"]]

    if isinstance(input_stream, str):
        f = open(input_stream, mode='r')
        is_file = True
    else:
        is_file = False

    def next_line():
        if is_file:
            return f.readline()
        else:
            return input_stream.pop(0) \
              if input_stream else None

    # Read the first line as a list of all fields.
    # Do some footwork to remove awkard characters.
    rfl = next_line()[1:].strip().split()
    reg = re.compile(r"\(\d+\)$")
    for pf in rfl:
        match = reg.search(pf)
        if match is None:
            fields.append(pf)
        else:
            fields.append(pf[:match.start()])

    # Now grab a bunch of things from the header.
    while True:
        line = next_line()
        if line is None:
            if ntrees_in_file:
                raise IOError(
                    f"Encountered enexpected EOF reading {input_stream}.")
            else:
                break
        elif not line.startswith("#"):
            if ntrees_in_file:
                arbor._size = int(line.strip())
                arbor._hoffset = f.tell()
            break

        # cosmological parameters
        if "Omega_M" in line:
            pars = line[1:].split(";")
            for j, par in enumerate(["omega_matter",
                                     "omega_lambda",
                                     "hubble_constant"]):
                v = float(pars[j].split(" = ")[1])
                setattr(arbor, par, v)

        # box size
        elif "Full box size" in line:
            pars = line.split("=")[1].strip().split()
            box = pars

        # These are lines describing the various fields.
        # Pull them apart and look for units.
        elif ":" in line:
            tfields, desc = line[1:].strip().split(":", 1)

            # Units are enclosed in parentheses.
            # Pull out what's enclosed and remove things like
            # "comoving" and "physical".
            if "(" in line and ")" in line:
                punits = desc[desc.find("(")+1:desc.rfind(")")]
                for rem in rems:
                    while rem in punits:
                        pre, mid, pos = punits.partition(rem)
                        punits = pre + pos
                try:
                    arbor.quan(1, punits)
                except UnitParseError:
                    punits = ""
            else:
                punits = ""

            # Multiple fields together on the same line.
            for sep in ["/", ","]:
                if sep in tfields:
                    tfields = tfields.split(sep)
                    break
            if not isinstance(tfields, list):
                tfields = [tfields]

            # Assign units and description.
            for tfield in tfields:
                fdb[tfield.lower()] = {"description": desc.strip(),
                                       "units": punits}

    if is_file:
        f.close()

    # Fill the field info with the units found above.
    for i, field in enumerate(fields):
        if "(" in field and ")" in field:
            cfield = field[:field.find("(")]
        else:
            cfield = field
        fi[field] = fdb.get(cfield.lower(),
                            {"description": "",
                             "units": ""})
        fi[field]["column"] = i

    arbor.box_size = arbor.quan(float(box[0]), box[1])
    return fi
