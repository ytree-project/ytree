"""
LHaloTreeArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2017, ytree development team
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from yt.funcs import \
    get_pbar
from yt.units.yt_array import \
    UnitParseError

from ytree.arbor.arbor import \
    Arbor
from ytree.arbor.tree_node import \
    TreeNode

from ytree.arbor.frontends.lhalotree.fields import \
    LHaloTreeFieldInfo
from ytree.arbor.frontends.lhalotree.io import \
    LHaloTreeTreeFieldIO

class LHaloTreeArbor(Arbor):
    """
    Arbors from consistent-trees output files.
    """

    _field_info_class = LHaloTreeFieldInfo
    _tree_field_io_class = LHaloTreeTreeFieldIO

    def _node_io_loop(self, func, *args, **kwargs):
        """
        This will get moved to the base class soon.
        It's a small optimization that keeps the file open
        when doing io for multiple trees.
        """
        f = open(self.filename, "r")
        kwargs["f"] = f
        super(LHaloTreeArbor, self)._node_io_loop(
            func, *args, **kwargs)
        f.close()

    def _parse_parameter_file(self):
        """
        Parse the file header, get things like:
        - cosmological parameters
        - box size
        - list of fields
        """

        # self.hubble_constant = ...
        # self.omega_matter = ...
        # self.omega_lambda = ...
        # self.box_size = self.quan(value, units)

        # a list of all fields on disk
        fields = []
        # a dictionary of information for each field
        # this can have specialized information for reading the field
        fi = {}
        # for example:
        # fi["mass"] = {"column": 4, "units": "Msun/h", ...}

        self.field_list = fields
        self.field_info.update(fi)

    def _plant_trees(self):
        """
        This is where we figure out how many trees there are,
        create the array to hold them, and instantiate a root
        tree_node for each tree.
        """

        # open file, count trees
        # ntrees = ...
        # self._trees = np.empty(ntrees, dtype=object)

        # for i in range(ntrees):
        #     # get a uid (unique id) from file or assign one
        #     uid = ...
        #     my_node = TreeNode(uid, arbor=self, root=True)
        #     # assign any helpful attributes, such as start
        #     # index in field arrays, etc.
        #     self._trees[i] = my_node

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Here's the ctrees example.
        File should end in .dat and have a line in the header
        with the string, "Consistent Trees".
        """
        fn = args[0]
        if not fn.endswith(".dat"): return False
        with open(fn, "r") as f:
            valid = False
            while True:
                line = f.readline()
                if line is None or not line.startswith("#"):
                    break
                if "Consistent Trees" in line:
                    valid = True
                    break
            if not valid: return False
        return True
