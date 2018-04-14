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

from yt.units.yt_array import \
    UnitParseError

from ytree.arbor.arbor import \
    CatalogArbor
from ytree.arbor.frontends.ahf.fields import \
    AHFFieldInfo
from ytree.arbor.frontends.ahf.io import \
    AHFDataFile

class AHFArbor(CatalogArbor):
    """
    Class for Arbors created from AHF out_*.list files.
    Use only descendent IDs to determine tree relationship.
    """

    _suffix = ".parameter"
    _field_info_class = AHFFieldInfo
    _data_file_class = AHFDataFile

    def _parse_parameter_file(self):
        df = AHFDataFile(self.filename, self)
        for attr in ["omega_matter",
                     "omega_lambda",
                     "hubble_constant"]:
            setattr(self, attr, getattr(df, attr))

        f = open("%s.AHF_halos" % df.data_filekey)
        line = f.readline()
        f.close()

        fields = [key[:key.rfind("(")]
                  for key in line[1:].strip().split()]
        fi = dict([(field, {"column": i})
                   for i, field in enumerate(fields)])

        # the scale factor comes from the catalog file header
        fields.append("redshift")
        fi["redshift"] = {"column": "header", "units": ""}

        self.field_list = fields
        self.field_info.update(fi)

    def _get_data_files(self):
        """
        Get all *.parameter files and sort them in reverse order.
        """
        prefix = self.filename.rsplit("_", 1)[0]
        suffix = self._suffix
        my_files = glob.glob("%s_*%s" % (prefix, suffix))
        # sort by catalog number
        my_files.sort(
            key=lambda x:
            self._get_file_index(x, prefix, suffix),
            reverse=True)
        self.data_files = \
          [self._data_file_class(f, self) for f in my_files]

    def _get_file_index(self, f, prefix, suffix):
        return int(f[f.find(prefix)+len(prefix)+1:f.rfind(suffix)]),

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
