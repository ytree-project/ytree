"""
AHFArbor io classes and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
import weakref

from ytree.arbor.io import \
    CatalogDataFile
from ytree.utilities.io import \
    f_text_block

class AHFDataFile(CatalogDataFile):
    def __init__(self, filename, arbor):
        self.filename = filename
        self.filekey = \
          self.filename[:self.filename.rfind(".parameter")]
        self._parse_header()
        self.data_filekey = "%s.z%.03f" % \
          (self.filekey, self.redshift)
        self.offsets = None
        self.arbor = weakref.proxy(arbor)

    def _parse_header(self):
        """
        Get header information from the .log file.
        Use that to get the name of the data file.
        """

        pars = {"Redshift": "redshift",
                "Omega0": "omega_matter",
                "OmegaLambda": "omega_lambda",
                "Hubble parameter": "hubble_constant"}
        npars = len(pars.keys())
        vals = {}

        f = open("%s.log" % self.filekey, "r")
        while True:
            line = f.readline()
            if line is None:
                break
            if len(vals.keys()) == npars:
                break
            for par in pars:
                key = pars[par]
                if key in vals:
                    continue
                if "%s:" % par in line:
                    val = float(line.split(":")[1])
                    vals[key] = val
        f.close()

        for par, val in vals.items():
            setattr(self, par, val)

    def open(self):
        self.fh = open(self.filename, "r")

    def _read_fields(self, fields, tree_nodes=None, dtypes=None):
        if dtypes is None:
            dtypes = {}

        fi = self.arbor.field_info
        hfields = [field for field in fields
                   if fi[field]["column"] == "header"]
        rfields = set(fields).difference(hfields)

        hfield_values = dict((field, getattr(self, field))
                             for field in hfields)

        if tree_nodes is None:
            field_data = dict((field, []) for field in fields)
            offsets = []
            self.open()
            f = self.fh
            f.seek(self._hoffset)
            file_size = self.file_size - self._hoffset
            for line, offset in f_text_block(f, file_size=file_size):
                offsets.append(offset)
                sline = line.split()
                for field in hfields:
                    field_data[field].append(hfield_values[field])
                for field in rfields:
                    dtype = dtypes.get(field, self._default_dtype)
                    field_data[field].append(dtype(sline[fi[field]["column"]]))
            self.close()
            if self.offsets is None:
                self.offsets = np.array(offsets)

        else:
            ntrees = len(tree_nodes)
            field_data = \
              dict((field,
                    np.empty(ntrees,
                             dtype=dtypes.get(field, self._default_dtype)))
                    for field in fields)

            # fields from the file header
            for field in hfields:
                field_data[field][:] = hfield_values[field]

            # fields from the actual data
            self.open()
            f = self.fh
            for i in range(ntrees):
                f.seek(self.offsets[tree_nodes[i]._fi])
                line = f.readline()
                sline = line.split()
                for field in rfields:
                    dtype = dtypes.get(field, self._default_dtype)
                    field_data[field][i] = dtype(sline[fi[field]["column"]])
            self.close()

        return field_data
