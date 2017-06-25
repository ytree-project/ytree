"""
RockstarArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import glob
import numpy as np
import warnings

from yt.units.yt_array import \
    UnitParseError

from ytree.arbor.arbor import \
    CatalogArbor
from ytree.arbor.frontends.rockstar.fields import \
    setup_field_groups

_rs_columns = (("halo_id",  (0,)),
               ("desc_id",  (1,)),
               ("mvir",     (2,)),
               ("rvir",     (5,)),
               ("position", (8, 9, 10)),
               ("velocity", (11, 12, 13)))
_rs_units = {"mvir": "Msun/h",
             "rvir": "kpc/h",
             "position": "Mpc/h",
             "velocity": "km/s"}
_rs_type = {"halo_id": np.int64,
            "desc_id": np.int64}
_rs_usecol = []
_rs_fields = {}
for field, col in _rs_columns:
    _rs_usecol.extend(col)
    _rs_fields[field] = np.arange(len(_rs_usecol)-len(col),
                                  len(_rs_usecol))

class RockstarArbor(CatalogArbor):
    """
    Class for Arbors created from Rockstar out_*.list files.
    Use only descendent IDs to determine tree relationship.
    """

    def _parse_parameter_file(self):
        fgroups = setup_field_groups()
        rems = ["%s%s%s" % (s[0], t, s[1])
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
        self.field_list = fields
        self.field_info.update(fi)

    def _get_all_files(self):
        """
        Get all out_*.list files and put them in reverse order.
        """
        prefix = self.filename.rsplit("_", 1)[0]
        suffix = ".list"
        my_files = glob.glob("%s_*%s" % (prefix, suffix))
        # sort by catalog number
        my_files.sort(key=lambda x:
                      int(x[x.find(prefix)+len(prefix)+1:x.rfind(suffix)]),
                      reverse=True)
        return my_files

    def _to_field_array(self, field, data):
        """
        Use field definitions from above to assign units
        for field arrays.
        """
        if field in _rs_units:
            self._field_data[field] = self.arr(data, _rs_units[field])
        else:
            self._field_data[field] = np.array(data)

    def _load_field_data(self, fn, offset):
        """
        Load field data using np.loadtxt.
        Create a redshift field and uid field.
        """
        with warnings.catch_warnings():
            # silence empty file warnings
            warnings.simplefilter("ignore", category=UserWarning,
                                  append=1, lineno=893)
            data = np.loadtxt(fn, unpack=True, usecols=_rs_usecol)
        z = self._read_parameters(fn)
        if data.size == 0:
            return 0

        if len(data.shape) == 1:
            data = np.reshape(data, (data.size, 1))
        n_halos = data.shape[1]
        self._field_data["redshift"].append(z * np.ones(n_halos))
        self._field_data["uid"].append(np.arange(offset, offset+n_halos))
        for field, cols in _rs_fields.items():
            if cols.size == 1:
                self._field_data[field].append(data[cols][0])
            else:
                self._field_data[field].append(np.rollaxis(data[cols], 1))
            if field in _rs_type:
                self._field_data[field][-1] = \
                  self._field_data[field][-1].astype(_rs_type[field])
        return n_halos

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .list.
        """
        fn = args[0]
        if not fn.endswith(".list"): return False
        return True

def _read_expansion_faction(filename):
    """
    Get the expansion factor from the file header.
    """
    f = open(filename, "r")
    while True:
        line = f.readline()
        if line is None or not line.startswith("#"):
            break
        if line.startswith("#a = "):
            f.close()
            return float(line.split("=")[1].strip())
    f.close()
    raise IOError(
        "Could not find expansion factor in header: %s." %
        filename)
