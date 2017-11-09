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
from ytree.arbor.frontends.lhalotree.utils import LHaloTreeReader


class LHaloTreeArbor(Arbor):
    """
    Arbors from consistent-trees output files.
    """

    _field_info_class = LHaloTreeFieldInfo
    _tree_field_io_class = LHaloTreeTreeFieldIO

    def __init__(self, *args, **kwargs):
        r"""Added reader class to allow fast access of header info."""
        reader_keys = ['parameter_file',
                       'header_size', 'nhalos_per_tree', 'read_header_func',
                       'item_dtype', 'scale_factor_file']
        reader_kwargs = dict()
        for k in reader_keys:
            if k in kwargs:
                reader_kwargs[k] = kwargs.pop(k)
        self._lhtreader = LHaloTreeReader(args[0], **reader_kwargs)
        super(LHaloTreeArbor, self).__init__(*args, **kwargs)
        kwargs.update(**reader_kwargs)

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

        for u in ['mass', 'vel', 'len']:
            setattr(self, '_lht_units_' + u,
                    getattr(self._lhtreader, 'units_' + u))
            # v, s = getattr(self._lhtreader, 'units_' + u).split()
            # setattr(self, '_lht_units_' + u, self.quan(float(v), s))

        self.hubble_constant = self._lhtreader.hubble_constant
        self.omega_matter = self._lhtreader.omega_matter
        self.omega_lambda = self._lhtreader.omega_lambda
        self.box_size = self.quan(self._lhtreader.box_size, self._lht_units_len)
        # self.box_size = self._lhtreader.box_size * self._lht_units_len

        # a list of all fields on disk
        fields = self._lhtreader.fields
        # a dictionary of information for each field
        # this can have specialized information for reading the field
        fi = {}
        # for example:
        # fi["mass"] = {"column": 4, "units": "Msun/h", ...}
        none_keys = ['Descendant', 'FirstProgenitor', 'NextProgenitor',
                     'FirstHaloInFOFgroup', 'NextHaloInFOFgroup',
                     'Len', 'Spin', 'MostBoundID',
                     'SnapNum', 'FileNr', 'SubhaloIndex',
                     'desc_uid', 'scale_factor']
        mass_keys = ['M_Mean200', 'Mvir', 'M_TopHat', 'SubHalfMass']
        dist_keys = ['Pos', 'x', 'y', 'z']
        velo_keys = ['Vel', 'VelDisp', 'Vmax', 'vx', 'vy', 'vz']
        for k in none_keys:
            fi[k] = {'units': ''}
        for k in mass_keys:
            fi[k] = {'units': self._lht_units_mass}
        for k in dist_keys:
            fi[k] = {'units': self._lht_units_len}
        for k in velo_keys:
            fi[k] = {'units': self._lht_units_vel}
            
        self.field_list = fields
        self.field_info.update(fi)

    def _plant_trees(self):
        """
        This is where we figure out how many trees there are,
        create the array to hold them, and instantiate a root
        tree_node for each tree.
        """

        # open file, count trees
        ntrees = self._lhtreader.ntrees
        self._trees = np.empty(ntrees, dtype=object)

        for i in range(ntrees):
            # get a uid (unique id) from file or assign one
            uid = self._lhtreader.get_lhalotree_uid(i)
            my_node = TreeNode(uid, arbor=self, root=True)
            # assign any helpful attributes, such as start
            # index in field arrays, etc.
            my_node._index_in_lht = i
            self._trees[i] = my_node

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Return True if we are able to initialize a reader.
        """
        try:
            kwargs['silent'] = True
            reader = LHaloTreeReader(*args, **kwargs)
        except BaseException:
            return False
        return True
