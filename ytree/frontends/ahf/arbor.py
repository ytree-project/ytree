"""
AHFArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import glob
import os
import re

from ytree.data_structures.arbor import \
    CatalogArbor
from ytree.frontends.ahf.fields import \
    AHFFieldInfo
from ytree.frontends.ahf.io import \
    AHFDataFile
from ytree.frontends.ahf.misc import \
    parse_AHF_file
from unyt.unit_registry import \
    UnitRegistry

class AHFArbor(CatalogArbor):
    """
    Arbor for Amiga Halo Finder data.
    """

    _suffix = ".parameter"
    _field_info_class = AHFFieldInfo
    _data_file_class = AHFDataFile

    def __init__(self, filename, log_filename=None,
                 hubble_constant=1.0, box_size=None,
                 omega_matter=None, omega_lambda=None):
        self.unit_registry = UnitRegistry()
        self.log_filename = log_filename
        self.hubble_constant = hubble_constant
        self.omega_matter = omega_matter
        self.omega_lambda = omega_lambda
        self._box_size_user = box_size
        super().__init__(filename)

    def _parse_parameter_file(self):
        df = AHFDataFile(self.filename, self)

        pars = {"simu.omega0": "omega_matter",
                "simu.lambda0": "omega_lambda",
                "simu.boxsize": "box_size"}
        log_filename = self.log_filename \
          if self.log_filename is not None else df.filekey + ".log"
        if os.path.exists(log_filename):
            vals = parse_AHF_file(log_filename, pars, sep=":")
            for attr in ["omega_matter",
                         "omega_lambda"]:
                setattr(self, attr, vals.get(attr))
            if "box_size" in vals:
                self.box_size = self.quan(vals["box_size"], "Mpc/h")

        if self._box_size_user is not None:
            self.box_size = self.quan(self._box_size_user, "Mpc/h")

        # fields from from the .AHF_halos files
        f = open(f"{df.data_filekey}.AHF_halos")
        line = f.readline()
        f.close()

        fields = [key[:key.rfind("(")]
                  for key in line[1:].strip().split()]
        fi = dict([(field, {"column": i, "file": "halos"})
                   for i, field in enumerate(fields)])

        # the scale factor comes from the catalog file header
        fields.append("redshift")
        fi["redshift"] = {"file": "header", "units": ""}

        # the descendent ids come from the .AHF_mtree files
        fields.append("desc_id")
        fi["desc_id"] = {"file": "mtree", "units": ""}

        self.field_list = fields
        self.field_info.update(fi)

    _fprefix = None
    @property
    def _prefix(self):
        if self._fprefix is None:
            # Match a patten of any characters, followed by some sort of
            # separator (e.g., "." or "_"), then a number, and eventually
            # the suffix.
            reg = re.search(rf"(^.+[^0-9a-zA-Z]+)\d+.+{self._suffix}$", self.filename)
            self._fprefix = reg.groups()[0]
        return self._fprefix

    def _get_data_files(self):
        """
        Get all *.parameter files and sort them in reverse order.
        """
        my_files = glob.glob(f"{self._prefix}*{self._suffix}")
        # sort by catalog number
        my_files.sort(
            key=lambda x:
            self._get_file_index(x))
        self.data_files = \
          [self._data_file_class(f, self) for f in my_files]

        # Set the mtree file for file i to that of i-1, since
        # AHF thinks in terms of progenitors and not descendents.
        for i, data_file in enumerate(self.data_files[:-1]):
            data_file.mtree_filename = \
              self.data_files[i+1].mtree_filename
        self.data_files[-1].mtree_filename = None
        self.data_files.reverse()

    def _get_file_index(self, f):
        reg = re.search(rf"{self._prefix}(\d+).+{self._suffix}$", self.filename)
        if not reg:
            raise RuntimeError(
                f"Could not locate index within file: {self.filename}.")
        return int(reg.groups()[0])

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File must end in .AHF_halos and have an associated
        .parameter file.
        """
        fn = args[0]
        if not fn.endswith(self._suffix):
            return False
        return True
