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

from ytree.arbor.arbor import \
    CatalogArbor
from ytree.arbor.frontends.ahf.fields import \
    AHFFieldInfo
from ytree.arbor.frontends.ahf.io import \
    AHFDataFile
from yt.units.unit_registry import \
    UnitRegistry

class AHFArbor(CatalogArbor):
    """
    Arbor for Amiga Halo Finder data.
    """

    _suffix = ".parameter"
    _field_info_class = AHFFieldInfo
    _data_file_class = AHFDataFile

    def __init__(self, filename, hubble_constant=1.0):
        self.unit_registry = UnitRegistry()
        self.hubble_constant = hubble_constant
        super(AHFArbor, self).__init__(filename)

    def _parse_parameter_file(self):
        df = AHFDataFile(self.filename, self)
        for attr in ["omega_matter",
                     "omega_lambda"]:
            setattr(self, attr, getattr(df, attr))
        self.box_size = self.quan(df.box_size, "Mpc/h")

        # fields from from the .AHF_halos files
        f = open("%s.AHF_halos" % df.data_filekey)
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
            self._fprefix = self.filename.rsplit("_", 1)[0]
        return self._fprefix

    def _get_data_files(self):
        """
        Get all *.parameter files and sort them in reverse order.
        """
        my_files = glob.glob("%s_*%s" % (self._prefix, self._suffix))
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
        return int(f[f.find(self._prefix) + len(self._prefix)+1:
                     f.rfind(self._suffix)]),

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File must end in .AHF_halos and have an associated
        .parameter file.
        """
        fn = args[0]
        if not fn.endswith(self._suffix):
            return False
        key = fn[:fn.rfind(self._suffix)]
        if not os.path.exists(key + ".log"):
            return False
        return True
