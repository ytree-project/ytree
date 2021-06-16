"""
TreeFrogArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py
import glob
import numpy as np
import os
import re

from yt.funcs import \
    get_pbar

from ytree.data_structures.arbor import \
    Arbor

from ytree.frontends.consistent_trees.arbor import \
    ConsistentTreesGroupArbor
from ytree.frontends.consistent_trees.utilities import \
    parse_ctrees_header
from ytree.frontends.treefrog.fields import \
    TreeFrogFieldInfo
from ytree.frontends.treefrog.io import \
    TreeFrogDataFile, \
    TreeFrogRootFieldIO, \
    TreeFrogTreeFieldIO
from ytree.utilities.exceptions import \
    ArborDataFileEmpty
from ytree.utilities.logger import \
    ytreeLogger as mylog

class TreeFrogArbor(Arbor):
    """
    Arbors loaded from consistent-trees data converted into HDF5.
    """

    _suffix = ".hdf5"
    _parameter_file_is_data_file = True
    _field_info_class = TreeFrogFieldInfo
    _root_field_io_class = TreeFrogRootFieldIO
    _tree_field_io_class = TreeFrogTreeFieldIO
    _node_io_attrs = ('_fi', '_si')

    _node_io_loop_prepare = ConsistentTreesGroupArbor._node_io_loop_prepare

    def _node_io_loop_start(self, data_file):
        data_file.open()

    def _node_io_loop_finish(self, data_file):
        data_file.close()

    def _get_data_files(self):
        self.data_files = [TreeFrogDataFile(f"{self._prefix}{self._suffix}.{i}")
                           for i in range(self._nfiles)]

    @property
    def _prefix(self):
        suffix = f".foreststats{self._suffix}"
        return self.parameter_filename[:-len(suffix)]

    def _parse_parameter_file(self):
        with h5py.File(self.parameter_filename, mode="r") as f:
            self._nfiles = f["Header"].attrs["NFiles"]
            self._nsnaps = f["Header"].attrs["NSnaps"]
            self._size = f["ForestInfo"].attrs["NForests"]
            self._file_count = f["ForestInfo"]["NForestsPerFile"][()]

        if self._nfiles < 1:
            mylog.warning(f"Dataset {self.parameter_filename} has no data files.")
            return

        fn = f"{self._prefix}{self._suffix}.0"
        if not os.path.exists(fn):
            raise RuntimeError(f"Data file not found: {fn}.")

        with h5py.File(fn, mode="r") as f:
            self.hubble_constant = f["Header/Simulation"].attrs["h_val"]
            self.omega_matter = f["Header/Simulation"].attrs["Omega_m"]
            self.omega_lambda = f["Header/Simulation"].attrs["Omega_Lambda"]
            self.box_size = self.quan(f["Header/Simulation"].attrs["Period"], "Mpc/h")
            if self._nsnaps < 1:
                mylog.warning(f"Dataset {self.parameter_filename} has no snapshots.")
                return

            self.units = {}
            for attr in ["Length_unit_to_kpc",
                         "Mass_unit_to_solarmass",
                         "Velocity_unit_to_kms"]:
                self.units[attr] = f["Header/Units"].attrs[attr]

            field_list = list(f["Snap_000"].keys())
            self._scale_factors = \
              np.array([f[f"Snap_{i:03d}"].attrs["scalefactor"]
                        for i in range(self._nsnaps)])

        self.field_list = field_list
        self.field_info.update({field: {} for field in field_list})

        self.field_list.append("scale_factor")
        self.field_info["scale_factor"] = {"source": "arbor"}

    def _plant_trees(self):
        if self.is_planted or self._size == 0:
            return

        with h5py.File(self.parameter_filename, mode="r") as f:
            self._node_info['uid'] = f["ForestInfo"]["ForestIDs"][()]
            self._node_info['_tree_size'] = f["ForestInfo"]["ForestSizes"][()]

        ei = self._file_count.cumsum()
        si = ei - self._file_count
        trees = np.arange(self._size)
        fi = np.digitize(trees, ei)
        # number of the file each forest lives in
        self._node_info['_fi'] = fi
        # index within that file each forest is at
        self._node_info['_si'] = trees - si[fi]

    def _setup_tree(self, tree_node, **kwargs):
        if self.is_setup(tree_node):
            return

        super()._setup_tree(tree_node, **kwargs)
        tree_node._desc_uids[0] = -1

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Should be an hdf5 file with a few key attributes.
        """
        fn = args[0]
        suffix = f".foreststats{self._suffix}"
        if not fn.endswith(suffix):
            return False
        if not h5py.is_hdf5(fn):
            return False

        info = \
          {"Header": ['FileSplittingCriteria', 'FilesSplitByForest',
                      'HaloCatalogBaseFileName', 'NFiles', 'NSnaps'],
          "ForestInfo": ['MaxForestFOFGroupID', 'MaxForestFOFGroupSize',
                         'MaxForestID', 'MaxForestSize', 'NForests']}

        with h5py.File(fn, mode='r') as f:
            for group, attrs in info.items():
                if group not in f:
                    return f
                for attr in attrs:
                    if attr not in f[group].attrs:
                        return False
        return True
