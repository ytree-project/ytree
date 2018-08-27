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

from ytree.arbor.frontends.ahf.misc import \
    parse_AHF_file
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
        Get header information from the .log and .parameter
        files. Use that to get the name of the data file.
        """

        pars = {"simu.omega0": "omega_matter",
                "simu.lambda0": "omega_lambda",
                "simu.boxsize": "box_size"}
        vals = parse_AHF_file(
            self.filekey + ".log", pars, sep=":")
        vals.update(parse_AHF_file(
            self.filekey + ".parameter", {"z": "redshift"}))

        for par, val in vals.items():
            setattr(self, par, val)

    def open(self):
        if self.fh is None:
            self.fh = open(self.halos_filename, "r")

    _links = None
    @property
    def links(self):
        if self._links is None:
            self._compute_links()
        return self._links

    def _compute_links(self):
        """
        Compute the tree from the graph.

        AHF computes a graph, where a given halo can
        have both multiple progenitors and descendents.

        Use the weight function to determine a unique
        descendent for each halo.

        descendent = max (M_ij = N_ij^2 / (N_i * N_j)),

        where:
           N_ij: number of shared particles
           N_i : number of particles in halo i
           N_j : number of particles in halo j
        """

        data = self._read_mtree()
        if data is None:
            self._links = -1
            return

        m = data["shared"]**2 / (data["prog_part"] * data["desc_part"])

        progids = np.unique(data["prog_id"])
        descids = np.empty(progids.size, dtype=progids.dtype)

        for i, progid in enumerate(progids):
            prf = data["prog_id"] == progid
            descids[i] = data["desc_id"][prf][m[prf].argmax()]
        udata = {"prog_id": progids, "desc_id": descids}

        self._links = udata

    def _read_mtree(self):
        """
        Read map of progenitors to descendents.
        This is the ".AHF_mtree" file.
        """
        if self.mtree_filename is None:
            return None

        data = defaultdict(list)
        descid = descpart = None

        f = open(self.mtree_filename, "r")
        for line, offset in f_text_block(f):
            if line.startswith("#"):
                continue
            if line[0].isdigit():
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

        afields = [field for field in fields
                   if fi[field].get("source") == "arbor"]
        my_fields = set(fields).difference(afields)

        # Separate fields into one that come from the file header,
        # the mtree file, and the halos file.
        data_fields = defaultdict(list)
        for field in my_fields:
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

        else:
            ntrees = len(tree_nodes)
            field_data = \
              dict((field, np.empty(
                  ntrees, dtype=dtypes.get(field, self._default_dtype)))
                  for field in afields + rfields + hfields)

            # fields from the file header
            for field in hfields:
                field_data[field][:] = hfield_values[field]

            # fields from arbor-related info
            if afields:
                for i in range(ntrees):
                    for field in afields:
                        dtype = dtypes.get(field, self._default_dtype)
                        field_data[field][i] = \
                          dtype(getattr(tree_nodes[i], field))

            # fields from the actual data
            if rfields:
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

        # use data from the mtree file to get descendent ids
        if tfields:
            links = self.links
            descids = np.empty(
                len(field_data["ID"]),
                dtype=dtypes.get(field, self._default_dtype))
            if self.links == -1:
                descids[:] = -1
            else:
                for i, hid in enumerate(field_data["ID"]):
                    inlink = hid == links["prog_id"]
                    if not inlink.any():
                        descids[i] = -1
                    else:
                        descids[i] = links["desc_id"][np.where(inlink)[0][0]]
            field_data["desc_id"] = descids

        for field in field_data:
            if isinstance(field_data[field], np.ndarray):
                continue
            field_data[field] = \
              np.array(field_data[field],
                       dtype=dtypes.get(field, self._default_dtype))

        return field_data
