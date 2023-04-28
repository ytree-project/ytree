"""
ColumnArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import glob
import numpy as np
import operator
import os
import re

from yt.funcs import \
    get_pbar

from ytree.data_structures.arbor import \
    Arbor

from ytree.frontends.column.io import \
    ColumnDataFile, \
    ColumnTreeFieldIO
from ytree.frontends.rockstar.arbor import \
    RockstarArbor

from ytree.utilities.exceptions import \
    ArborDataFileEmpty
from ytree.utilities.io import \
    f_text_block

class ColumnArbor(Arbor):
    """
    Arbors loaded from consistent-trees tree_*.dat files.
    """

    _tree_field_io_class = ColumnTreeFieldIO
    _default_dtype = np.float32
    _node_io_attrs = ('_si',)

    def __init__(self, filename, sep=","):
        self.sep = sep
        super().__init__(filename)

    def _get_data_files(self):
        self.data_files = [ColumnDataFile(self.filename)]

    def _parse_parameter_file(self, filename=None):
        if filename is None:
            filename = self.filename

        with open(filename, mode="r") as f:
            ldata = []
            for i in range(3):
                line = f.readline().strip()
                # remove comment characters
                ldata.append(re.search("^#+\s*(\S.*)$", line).groups()[0])
            self._hoffset = f.tell()

        fields = [_.strip() for _ in ldata[0].split(self.sep)]
        dtypes = [_.strip() for _ in ldata[1].split(self.sep)]
        units  = [_.strip() for _ in ldata[2].split(self.sep)]
        fi = {}
        for i, (field, dtype, unit) in enumerate(zip(fields, dtypes, units)):
            my_unit = None if unit == "None" else unit
            fi[field] = {"column": i, "units": my_unit, "dtype": eval(dtype)}

        try:
            fi["uid"]["dtype"] = np.int64
            fi["desc_uid"]["dtype"] = np.int64
        except KeyError:
            raise IOError(f"{filename} is missing either uid or desc_uid fields.")

        self.field_list = list(fi.keys())
        self.field_info.update(fi)

    def _plant_trees(self):
        if self.is_planted or self._size == 0:
            return

        data_file = self.data_files[0]
        data_file.open()
        data_file.fh.seek(self._hoffset)

        itree = 0
        fi = self.field_info
        col_uid = fi["uid"]["column"]
        typ_uid = fi["uid"]["dtype"]
        col_des = fi["desc_uid"]["column"]
        typ_des = fi["desc_uid"]["dtype"]

        roots = []
        root_offsets = []

        # these two are for nonroots only
        desc_uids = {}
        offsets = {}

        for line, loc in f_text_block(
                data_file.fh, pbar_string="Loading tree roots"):

            online = line.split(self.sep)
            uid = typ_uid(online[col_uid])
            desc_uid = typ_des(online[col_des])

            if desc_uid == -1:
                roots.append(uid)
                root_offsets.append(loc)
            else:
                desc_uids[uid] = desc_uid
                offsets[uid] = loc

        n_nonroots = len(desc_uids)
        uids = np.array(list(desc_uids.keys()) + roots)
        desc_uids = np.array(list(desc_uids.values()))
        # look for any nodes with missing descendents
        missing = np.in1d(desc_uids, uids, invert=True)
        # need to address only up to n_nonroots since
        # uids has everything and desc_uids has only nonroots
        missing_uids = uids[:n_nonroots][missing]

        root_uids = np.concatenate([np.array(roots), missing_uids])
        root_offsets = np.concatenate(
            [np.array(root_offsets),
             np.array([offsets[uid] for uid in missing_uids])])

        self._size = root_uids.size
        self._node_info["uid"][:] = root_uids
        self._node_info["_si"][:] = root_offsets

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .col and start with three lines of the
        following format:
        # <fieldname><sep><fieldname><sep><fieldname>...
        # <type><sep><type><sep><type>
        # <units><sep><units><sep><units>

        For example, if sep=",":
        # uid, desc_uid, mass, redshift
        # int, int, float, float
        # "", "", "Msun", ""
        """
        fn = args[0]
        sep = kwargs.get("sep", ",")
        if not fn.endswith(".col"):
            return False
        with open(fn, "r") as f:
            for i in range(3):
                line = f.readline()
                if not line.startswith("#"):
                    return False

                if sep not in line:
                    return False
        return True

class ColumnGroupArbor(ColumnArbor):
    """
    Arbors loaded from consistent-trees locations.dat files.
    """

    def _get_data_files(self):
        pass

    def _parse_parameter_file(self):
        f = open(self.filename, 'r')
        f.readline()
        self._hoffset = f.tell()
        line = f.readline()
        if not line:
            raise ArborDataFileEmpty(self.filename)

        fn = os.path.join(self.directory, line.split()[3])
        super()._parse_parameter_file(filename=fn, ntrees_in_file=False)

    def _plant_trees(self):
        if self.is_planted:
            return

        f = open(self.filename, 'r')
        f.seek(self._hoffset)
        ldata = list(map(
            lambda x: [int(x[0]), int(x[1]), int(x[2]), x[3], len(x[0])],
            [line.split() for line, _ in f_text_block(f, pbar_string='Reading locations')]
            ))
        f.close()

        self._size = len(ldata)

        # It's faster to create and sort arrays and then sort ldata
        # for some reason.
        dfns = np.unique([datum[3] for datum in ldata])
        dfns.sort()
        fids = np.array([datum[1] for datum in ldata])
        fids.sort()
        ufids = np.unique(fids)
        ufids.sort()

        # Some data files may be empty and so unlisted.
        # Make sure file ids and names line up.
        data_files = [None]*(ufids.max()+1)
        for i,fid in enumerate(ufids):
            data_files[fid] = dfns[i]
        self.data_files = \
          [None if fn is None
           else ColumnDataFile(os.path.join(self.directory, fn))
           for fn in data_files]

        ldata.sort(key=operator.itemgetter(1, 2))
        pbar = get_pbar("Loading tree roots", self._size)

        # Set end offsets for each tree.
        # We don't get them from the location file.
        lkey = len("tree ")+3 # length of the separation line between trees
        same_file = np.diff(fids, append=fids[-1]+1) == 0

        for i, tdata in enumerate(ldata):
            self._node_info['uid'][i] = tdata[0]
            self._node_info['_fi'][i] = tdata[1]
            self._node_info['_si'][i] = tdata[2]
            # Get end index from next tree.
            if same_file[i]:
                self._node_info['_ei'][i] = ldata[i+1][2] - lkey - tdata[4]
            pbar.update(i+1)
        pbar.finish()

        # Get end index for last trees in files.
        for i in np.where(~same_file)[0]:
            data_file = self.data_files[fids[i]]
            data_file.open()
            data_file.fh.seek(0, 2)
            self._node_info['_ei'][i] = data_file.fh.tell()
            data_file.close()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .dat and have a line in the header
        with the string, "Consistent Trees".
        """
        fn = args[0]
        if not os.path.basename(fn) == 'locations.dat':
            return False
        with open(fn, "r") as f:
            valid = False
            while True:
                line = f.readline()
                if line is None or not line.startswith("#"):
                    break
                if "TreeRootID FileID Offset Filename" in line:
                    valid = True
            if not valid:
                return False
        return True
