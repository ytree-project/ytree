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

from collections import defaultdict
import numpy as np
import os
import weakref

from ytree.arbor.io import \
    CatalogDataFile
from ytree.utilities.io import \
    f_text_block

class AHFDataFile(CatalogDataFile):
    def __init__(self, filename, arbor):
        self.filename = filename
        self.filekey = self.filename[:self.filename.rfind(".parameter")]
        self._parse_header()
        self.data_filekey = "%s.z%.03f" % (self.filekey, self.redshift)
        self.halos_filename = self.data_filekey + ".AHF_halos"
        self.mtree_filename = self.data_filekey + ".AHF_mtree"
        if not os.path.exists(self.mtree_filename):
            self.mtree_filename = None
        self.fh = None
        self._parse_data_header()
        self.offsets = None
        self.arbor = weakref.proxy(arbor)

    def _parse_data_header(self):
        """
        Get header sizes from the two data files ending
        in .AHF_halos and .AHF_mtree.
        """

        self.open()
        fh = self.fh
        fh.seek(0, 2)
        self.file_size = fh.tell()
        fh.seek(0)
        for line, loc in f_text_block(fh):
            if not line.startswith("#"):
                loc -= len(line) + 1
                break
        self._hoffset = loc + len(line) + 1
        self.close()

    def _parse_header(self):
        """
        Get header information from the .log file.
        Use that to get the name of the data file.
        """

        pars = {"Redshift": "redshift",
                "Omega0": "omega_matter",
                "OmegaLambda": "omega_lambda",
                "Hubble parameter": "hubble_constant",
                "Boxsize": "box_size"}
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
        if self.fh is None:
            self.fh = open(self.halos_filename, "r")

    def _compute_tree(self):
        """
        Compute the tree from the graph.

        AHF computes a graph, where a given halo can
        have both multiple progenitors and descendents.

        Use the weight function to determine a unique
        descendant for each halo.

        descendent = max (M_ij = N_ij^2 / (N_i * N_j)),

        where:
           N_ij: number of shared particles
           N_i : number of particles in halo i
           N_j : number of particles in halo j
        """

        data = self._read_mtree()
        if data is None:
            return None

        m = data["shared"]**2 / (data["prog_part"] * data["desc_part"])

        progids = np.unique(data["prog_id"])
        descids = np.empty(progids.size, dtype=progids.dtype)

        for i, progid in enumerate(progids):
            prf = data["prog_id"] == progid
            descids[i] = data["desc_id"][prf][m[prf].argmax()]
        udata = {"prog_id": progids, "desc_id": descids}

        return udata

    def _read_mtree(self):
        if self.mtree_filename is None:
            return None

        data = defaultdict(list)
        descid = descpart = None

        f = open(self.mtree_filename, "r")
        for line, offset in f_text_block(f):
            if line.startswith("#"):
                continue
            if line[0].isnumeric():
                oline = line.split()
                descid = int(oline[0])
                descpart = int(oline[1])
            else:
                oline = line.split()
                data["shared"].append(int(oline[0]))
                data["prog_id"].append(int(oline[1]))
                data["prog_part"].append(int(oline[2]))
                data["desc_id"].append(descid)
                data["desc_part"].append(descpart)
        f.close()

        if not data:
            return None

        for field in data:
            data[field] = np.array(data[field])
        return data

    def _read_fields(self, fields, tree_nodes=None, dtypes=None):
        if dtypes is None:
            dtypes = {}

        fi = self.arbor.field_info
        # Separate fields into one that come from the file header,
        # the mtree file, and the halos file.
        data_fields = defaultdict(list)
        for field in fields:
            source = fi[field]["file"]
            data_fields[source].append(field)

        hfields = data_fields.pop("header", [])
        hfield_values = dict((field, getattr(self, field))
                             for field in hfields)
        rfields = data_fields.pop("halos", [])
        tfields = data_fields.pop("mtree", [])
        # If we needs desc_ids, make sure to get IDs so
        # we can link them.
        if tfields:
            links = self._compute_tree()
            if "ID" not in rfields:
                rfields.append("ID")

        if tree_nodes is None:
            field_data = dict((field, []) for field in rfields + hfields)
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

            if tfields:
                descids = \
                  np.empty(len(field_data["ID"]),
                          dtype=dtypes.get(field, self._default_dtype))
                if links is None:
                    descids[:] = -1
                else:
                    for i, hid in enumerate(field_data["ID"]):
                        inlink = hid == links["prog_id"]
                        if not inlink.any():
                            descids[i] = -1
                        else:
                            descids[i] = \
                          links["desc_id"][np.where(inlink)[0][0]]
                field_data["desc_id"] = descids

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

        for field in field_data:
            if isinstance(field_data[field], np.ndarray):
                continue
            field_data[field] = \
              np.array(field_data[field],
                       dtype=dtypes.get(field, self._default_dtype))

        return field_data