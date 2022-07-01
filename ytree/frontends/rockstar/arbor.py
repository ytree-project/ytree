"""
RockstarArbor class and member functions



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

from unyt.exceptions import \
    UnitParseError

from ytree.data_structures.arbor import \
    CatalogArbor
from ytree.frontends.rockstar.fields import \
    RockstarFieldInfo, \
    setup_field_groups
from ytree.frontends.rockstar.io import \
    RockstarDataFile

class RockstarArbor(CatalogArbor):
    """
    Class for Arbors created from Rockstar out_*.list files.
    Use only descendent IDs to determine tree relationship.
    """

    _field_info_class = RockstarFieldInfo
    _data_file_class = RockstarDataFile
    _default_dtype = np.float32

    def _parse_parameter_file(self):
        fgroups = setup_field_groups()
        rems = [f"{s[0]}{t}{s[1]}"
                for s in [("(", ")"), ("", "")]
                for t in ["physical, peculiar",
                          "comoving", "physical"]]

        f = open(self.filename, "r")
        # Read the first line as a list of all fields.
        fields = f.readline()[1:].strip().split()

        # Get box size, cosmological parameters, and units.
        while True:
            line = f.readline()
            if line is None or not line.startswith("#"):
                break
            elif line.startswith("#Om = "):
                pars = line[1:].split(";")
                for j, par in enumerate(["omega_matter",
                                         "omega_lambda",
                                         "hubble_constant"]):
                    v = float(pars[j].split(" = ")[1])
                    setattr(self, par, v)
            elif line.startswith("#Box size:"):
                pars = line.split(":")[1].strip().split()
                self.box_size = self.quan(float(pars[0]), pars[1])
            # Looking for <quantities> in <units>
            elif line.startswith("#Units:"):
                if " in " not in line: continue
                quan, punits = line[8:].strip().split(" in ", 2)
                for rem in rems:
                    while rem in punits:
                        pre, mid, pos = punits.partition(rem)
                        punits = pre + pos
                try:
                    self.quan(1, punits)
                except UnitParseError:
                    punits = ""
                for group in fgroups:
                    if group.in_group(quan):
                        group.units = punits
                        break
        f.close()

        fi = {}
        for i, field in enumerate(fields):
            for group in fgroups:
                units = ""
                if group.in_group(field):
                    units = getattr(group, "units", "")
                    break
            fi[field] = {"column": i, "units": units}

        # the scale factor comes from the catalog file header
        fields.append("scale_factor")
        fi["scale_factor"] = {"source": "header", "units": ""}

        self.field_list = fields
        self.field_info.update(fi)

    def _get_data_files(self):
        """
        Get all out_*.list files and sort them in reverse order.
        """
        reg = re.search(r"_\d+[_\.]", self.basename)
        prefix = self.basename[:reg.start()+1]
        suffix = self.basename[reg.end()-1:]

        freg = re.compile(rf"{prefix}\d+{suffix}")
        my_files = [os.path.join(self.directory, f)
                    for f in os.listdir(self.directory)
                    if freg.match(f)]

        # sort by catalog number
        my_files.sort(
            key=lambda x:
            self._get_file_index(x, prefix, suffix),
            reverse=True)
        self.data_files = \
          [self._data_file_class(f, self) for f in my_files]

    def _get_file_index(self, f, prefix, suffix):
        return int(f[f.find(prefix)+len(prefix):f.rfind(suffix)])

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .list.
        """
        fn = args[0]
        if not os.path.basename(fn).startswith("out") or \
          not fn.endswith(".list"):
            return False
        # filter out non-integers
        reg = re.search(r"_\d+[_\.]\D", fn)
        if reg is None:
            return False
        return True
