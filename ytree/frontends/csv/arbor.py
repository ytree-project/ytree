"""
CSVArbor class and member functions



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

from yt.funcs import get_pbar

from ytree.data_structures.arbor import CatalogArbor
from ytree.data_structures.tree_node import TreeNode

from ytree.frontends.csv.io import CSVDataFile

from ytree.utilities.io import f_text_block

from numpy.dtypes import StringDType

field_data_types = {
    "FLOAT": float,
    "INT": int,
    "STR": StringDType(),
}


class CSVArbor(CatalogArbor):
    """
    Arbors loaded from consistent-trees tree_*.dat files.
    """

    _data_file_class = CSVDataFile
    _has_uids = True
    _default_dtype = np.float32
    _node_con_attrs = ()
    _node_io_attrs = ()
    _ancestors = None

    def __init__(self, filename, sep=","):
        self.sep = sep
        super().__init__(filename)

    def _get_data_files(self):
        self.data_files = [CSVDataFile(self.filename, self)]

    def _parse_parameter_file(self, filename=None):
        if filename is None:
            filename = self.filename

        with open(filename, mode="r") as f:
            ldata = []
            for i in range(3):
                ldata.append(f.readline().strip()[1:].split(self.sep))
            self._hoffset = f.tell()

        lens = [len(_) for _ in ldata]
        if min(lens) != max(lens):
            raise RuntimeError("Header lines must have same number of values.")

        fields, dtypes, units = ldata
        fi = {}
        for i, (field, dtype, unit) in enumerate(zip(fields, dtypes, units)):
            my_unit = "" if unit == "None" else unit
            fi[field] = {
                "column": i,
                "units": my_unit,
                "dtype": field_data_types[dtype],
            }

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

        for line, loc in f_text_block(data_file.fh, pbar_string="Loading tree roots"):
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
        missing = np.isin(nr_desc_uids, uids, invert=True)
        # need to address only up to n_nonroots since
        # uids has everything and desc_uids has only nonroots
        missing_uids = uids[:n_nonroots][missing]
        for uid in missing_uids:
            del desc_uids[uid]

        trees = []
        for uid, offset in zip(roots, root_offsets):
            my_node = TreeNode(uid, arbor=self, root=True)
            my_node._offset = offset
            my_node.data_file = self.data_files[0]
            trees.append(my_node)

        for uid in missing_uids:
            offset = offsets.pop(uid)
            my_node = TreeNode(uid, arbor=self, root=True)
            my_node._offset = offset
            my_node.data_file = self.data_files[0]
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

        # If we have already done this, get out of here.
        if self._ancestors is not None:
            return

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
            my_node.data_file = self.data_files[0]
            ancestors[desc_uid].append(my_node)
            pbar.update(i + 1)
        pbar.finish()

        self._ancestors = ancestors
        del self._desc_uids, self._offsets

    def _grow_tree(self, tree_node):
        """
        We don't actually attach the tree's _ancestors during planting,
        so do it here.
        """

        self._get_ancestors(tree_node)

    def _get_ancestors(self, tree_node):
        """
        Get this tree's ancestors from the main ancestor dictionary.

        This arbor stores every tree's ancestors in a dictionary.
        When we finally need it, grab it from the arbor and attach
        it to the tree.
        """

        self._build_trees()
        if tree_node._ancestors is None:
            tree_node._ancestors = self._ancestors.pop(tree_node.uid, [])
        for node in tree_node._ancestors:
            node._descendent = tree_node
            self._get_ancestors(node)

    def _setup_tree(self, tree_node):
        if self.is_setup(tree_node):
            return

        self._get_ancestors(tree_node)
        super()._setup_tree(tree_node)

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .csv and start with three lines of the
        following format.
        #<fieldname>,<fieldname>,<fieldname>
        #<type>,<type>,<type>
        #<units>,<units>,<units>

        For example:
        #uid,desc_uid,mass,redshift
        #int,int,float,float
        #None,None,"Msun",None
        """
        fn = args[0]
        sep = kwargs.get("sep", ",")
        if not fn.endswith(".csv"):
            return False
        with open(fn, "r") as f:
            for i in range(3):
                line = f.readline()
                if not line.startswith("#"):
                    return False

                if sep not in line:
                    return False
        return True
