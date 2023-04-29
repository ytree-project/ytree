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

from collections import defaultdict
import glob
import numpy as np
import operator
import os
import re

from yt.funcs import get_pbar

from ytree.data_structures.arbor import CatalogArbor
from ytree.data_structures.tree_node import TreeNode

from ytree.frontends.column.io import \
    ColumnDataFile, \
    ColumnTreeFieldIO
from ytree.frontends.rockstar.arbor import \
    RockstarArbor

from ytree.utilities.exceptions import \
    ArborDataFileEmpty
from ytree.utilities.io import f_text_block

class ColumnArbor(CatalogArbor):
    """
    Arbors loaded from consistent-trees tree_*.dat files.
    """

    _tree_field_io_class = ColumnTreeFieldIO
    _has_uids = True
    _default_dtype = np.float32
    _node_con_attrs = ()
    _node_io_attrs = ()

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
        nr_desc_uids = np.array(list(desc_uids.values()))
        # look for any nodes with missing descendents
        missing = np.in1d(nr_desc_uids, uids, invert=True)
        # need to address only up to n_nonroots since
        # uids has everything and desc_uids has only nonroots
        missing_uids = uids[:n_nonroots][missing]
        for uid in missing_uids:
            del desc_uids[uid]

        trees = []
        for uid, offset in zip(roots, root_offsets):
            my_node = TreeNode(uid, arbor=self, root=True)
            my_node._offset = offset
            trees.append(my_node)

        for uid in missing_uids:
            offset = offsets.pop(uid)
            my_node = TreeNode(uid, arbor=self, root=True)
            my_node._offset = offset
            trees.append(my_node)

        self._size = len(trees)
        self._trees = np.array(trees)

        # these are for the nonroot nodes
        # we will construct them later when they are needed
        self._desc_uids = desc_uids
        self._offsets = offsets

    def _build_trees(self):
        """
        Resolve the dictionary of desc_uids into trees.
        """

        if self.size < 1:
            return

        desc_uids = getattr(self, "_desc_uids", None)
        if desc_uids is None:
            return

        offsets = getattr(self, "_offsets")
        ancestors = defaultdict(list)
        pbar = get_pbar("Building trees", len(desc_uids))
        for i, (uid, desc_uid) in enumerate(desc_uids.items()):
            my_node = TreeNode(uid, arbor=self)
            my_node._offset = offsets[uid]
            ancestors[desc_uid].append(my_node)
            pbar.update(i)
        pbar.finish()

        self._ancestors = ancestors
        del self._desc_uids, self._offsets

    def _get_ancestors(self, tree_node):
        tree_node._ancestors = self._ancestors.pop(tree_node.uid, [])
        for node in tree_node._ancestors:
            node._descendent = tree_node
            self._get_ancestors(node)

    def _setup_tree(self, tree_node):
        if self.is_setup(tree_node):
            return

        self._build_trees()
        self._get_ancestors(tree_node)
        super()._setup_tree(tree_node)

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
