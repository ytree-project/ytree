"""
AHFArbor io classes and member functions



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from collections import defaultdict
import numpy as np
import os
import re
import weakref

from ytree.frontends.ahf.misc import parse_AHF_file
from ytree.data_structures.io import CatalogDataFile
from ytree.utilities.io import f_text_block
from ytree.utilities.misc import fround


class AHFDataFile(CatalogDataFile):
    _redshift_precision = 3

    def __init__(self, filename, arbor):
        self.arbor = weakref.proxy(arbor)
        self.filename = filename
        self._catalog_index = arbor._get_file_index(filename)
        self.filekey = self.filename[: self.filename.rfind(self.arbor._par_suffix)]
        self._parse_header()

        rprec = self._redshift_precision
        rstr = r"\.z\d\.\d\{%d\}" % rprec
        res = re.search(rstr, self.filekey)
        if res:
            self.data_filekey = self.filekey[: res.end()]
        else:
            zfmt = f".0{rprec}f"
            for inc in [0, -(10**-rprec)]:
                my_z = format(fround(self.redshift, decimals=rprec) + inc, zfmt)
                fkey = f"{self.filekey}.z{my_z}"
                if os.path.exists(fkey + self.arbor._data_suffix):
                    self.data_filekey = fkey
                    break

            if not hasattr(self, "data_filekey"):
                raise FileNotFoundError(
                    f"Cannot find data file: {fkey + self.arbor._data_suffix}."
                )

        self._get_other_filenames()
        self.fh = None
        self._parse_data_header()
        self.offsets = None

    def _get_other_filenames(self):
        """
        Figure out the various additional filenames we're going to need here.

        If prefixes for the ahf and mtree files have been set, then we need to
        look out for this and adjust.
        """

        self.halos_filename = self.data_filekey + self.arbor._data_suffix

        if self.arbor._ahf_prefix is None:
            mtree_key = self.data_filekey
        else:
            # First, strip of the directory
            mtree_key = re.sub(
                f"^{self.arbor.directory}{os.path.sep}", "", self.data_filekey
            )
            # Now, substitute the prefixes
            mtree_key = re.sub(
                f"^{self.arbor._ahf_prefix}", f"{self.arbor._mtree_prefix}", mtree_key
            )
            # Return the directory
            mtree_key = os.path.join(self.arbor.directory, mtree_key)

        self.mtree_filename = mtree_key + self.arbor._mtree_suffix
        if not os.path.exists(self.mtree_filename):
            self.mtree_filename = None

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

        vals = parse_AHF_file(self.filekey + ".parameter", {"z": "redshift"})

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

        m = data["shared"] ** 2 / (data["prog_part"] * data["desc_part"])

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

    def _read_data_default(self, rfields, dtypes):
        if not rfields:
            return {}

        fi = self.arbor.field_info
        field_data = self._create_field_arrays(rfields, dtypes)
        offsets = []

        self.open()
        f = self.fh
        f.seek(self._hoffset)
        file_size = self.file_size - self._hoffset
        for line, offset in f_text_block(f, file_size=file_size):
            offsets.append(offset)
            sline = line.split()
            for field in rfields:
                dtype = dtypes[field]
                field_data[field].append(dtype(sline[fi[field]["column"]]))
        self.close()

        if self.offsets is None:
            self.offsets = np.array(offsets)

        return field_data

    def _read_data_select(self, rfields, tree_nodes, dtypes):
        if not rfields:
            return {}

        fi = self.arbor.field_info
        nt = len(tree_nodes)
        field_data = self._create_field_arrays(rfields, dtypes, size=nt)

        self.open()
        f = self.fh

        for i in range(nt):
            f.seek(self.offsets[tree_nodes[i]._fi])
            line = f.readline()
            sline = line.split()
            for field in rfields:
                dtype = dtypes[field]
                field_data[field][i] = dtype(sline[fi[field]["column"]])
        self.close()

        return field_data

    def _get_mtree_fields(self, tfields, dtypes, field_data):
        """
        Use data from the mtree file to get descendent ids.
        """

        if not tfields:
            return

        links = self.links
        descids = np.empty(len(field_data["ID"]), dtype=dtypes["desc_id"])

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

    def _read_fields(self, fields, tree_nodes=None, dtypes=None):
        if dtypes is None:
            dtypes = {}

        fi = self.arbor.field_info

        afields = [field for field in fields if fi[field].get("source") == "arbor"]
        my_fields = set(fields).difference(afields)

        # Separate fields into one that come from the file header,
        # the mtree file, and the halos file.
        data_fields = defaultdict(list)
        for field in my_fields:
            source = fi[field]["file"]
            data_fields[source].append(field)

        hfields = data_fields.pop("header", [])
        rfields = data_fields.pop("halos", [])
        tfields = data_fields.pop("mtree", [])
        # If we needs desc_ids, make sure to get IDs so
        # we can link them.
        if tfields:
            if "ID" not in rfields:
                rfields.append("ID")
                dtypes.update(self.arbor._node_io._determine_dtypes(["ID"]))

        field_data = {}
        if tree_nodes is None:
            field_data.update(self._read_data_default(rfields, dtypes))

        else:
            # fields from the actual data
            field_data.update(self._read_data_select(rfields, tree_nodes, dtypes))

            # fields from arbor-related info
            field_data.update(self._get_arbor_fields(afields, tree_nodes, dtypes))

            # fields from the file header
            field_data.update(self._get_header_fields(hfields, tree_nodes, dtypes))

        # use data from the mtree file to get descendent ids
        self._get_mtree_fields(tfields, dtypes, field_data)

        return field_data


class AHFCRMDataFile(AHFDataFile):
    def _compute_links(self):
        """
        Read the CRMratio2 file.
        """

    def _compute_links(self):
        self.arbor._compute_links()

    def _get_mtree_fields(self, tfields, dtypes, field_data):
        if not tfields:
            return

        my_ids = field_data["ID"]
        field_data["desc_id"] = descids = np.full(
            len(my_ids), -1, dtype=dtypes["desc_id"]
        )

        if not self.links:
            return

        for i in range(descids.size):
            descids[i] = self.links.get(my_ids[i], -1)
