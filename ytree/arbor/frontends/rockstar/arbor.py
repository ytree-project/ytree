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

from ytree.arbor.arbor import \
    CatalogArbor

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

    def _read_parameters(self, filename):
        """
        Read header file to get cosmological parameters
        and modify unit registry for hubble constant.
        """
        get_pars = not hasattr(self, "hubble_constant")
        f = open(filename, "r")
        while True:
            line = f.readline()
            if line is None or not line.startswith("#"):
                break
            if get_pars and line.startswith("#Om = "):
                pars = line[1:].split(";")
                for j, par in enumerate(["omega_matter",
                                         "omega_lambda",
                                         "hubble_constant"]):
                    v = float(pars[j].split(" = ")[1])
                    setattr(self, par, v)
            if get_pars and line.startswith("#Box size:"):
                pars = line.split(":")[1].strip().split()
                box = pars
            if line.startswith("#a = "):
                a = float(line.split("=")[1].strip())
        f.close()
        if get_pars:
            self.box_size = self.quan(float(box[0]), box[1])
        return 1. / a - 1.

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
