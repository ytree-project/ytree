"""
LHaloTreeArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
import glob

from yt.funcs import \
    get_pbar
from unyt.exceptions import \
    UnitParseError

from ytree.data_structures.arbor import \
    Arbor

from ytree.frontends.lhalotree.fields import \
    LHaloTreeFieldInfo
from ytree.frontends.lhalotree.io import \
    LHaloTreeTreeFieldIO, LHaloTreeRootFieldIO
from ytree.frontends.lhalotree.utils import \
    LHaloTreeReader
from ytree.utilities.logger import \
    ytreeLogger


class LHaloTreeArbor(Arbor):
    """
    Arbors for LHaloTree data.
    """

    _field_info_class = LHaloTreeFieldInfo
    _tree_field_io_class = LHaloTreeTreeFieldIO
    _root_field_io_class = LHaloTreeRootFieldIO
    _default_dtype = np.float32
    _node_io_attrs = ('_lht', '_index_in_lht')

    def __init__(self, *args, **kwargs):
        r"""Added reader class to allow fast access of header info."""
        reader_keys = ['parameters', 'parameter_file',
                       'scale_factors', 'scale_factor_file',
                       'header_size', 'nhalos_per_tree', 'read_header_func',
                       'item_dtype']
        reader_kwargs = dict()
        for k in reader_keys:
            if k in kwargs:
                reader_kwargs[k] = kwargs.pop(k)
        self._lht0 = LHaloTreeReader(args[0], **reader_kwargs)
        super().__init__(*args, **kwargs)
        kwargs.update(**reader_kwargs)
        lht0 = self._lht0
        files = sorted(glob.glob(lht0.filepattern))
        self._lhtfiles = [None for _ in files]
        self._lhtfiles[lht0.fileindex] = lht0
        if len(files) > 1:
            if ((('header_size' in reader_kwargs) or  # pragma: no cover
                 ('nhalos_per_tree' in reader_kwargs))):
                raise RuntimeError("Cannot use 'header_size' or 'nhalos_per_tree' " +
                                   "for trees split across multiple files. Use " +
                                   "'read_header_func' instead.")
            reader_kwargs.update(parameters=lht0.parameters,
                                 scale_factors=lht0.scale_factors,
                                 item_dtype=lht0.item_dtype,
                                 silent=True)
            for f in files:
                if f == lht0.filename:
                    continue
                ilht = LHaloTreeReader(f, **reader_kwargs)
                self._lhtfiles[ilht.fileindex] = ilht
        # Assert files are there
        for f in self._lhtfiles:
            if f is None:  # pragma: no cover
                raise RuntimeError("Not all files were read.")

    # NOTE: LHaloTree is currently using np.memmap so it dosn't need
    # fd to be passed. If this causes memory issues for larger trees,
    # the below functions allow a file descriptor to be checked and updated
    # as needed to prevent unnecessary open/close operations when accessing
    # nodes in the same file. Alternatively, see io.py for an option that
    # caches the file descriptor any time a field is read.

    # def _func_update_file(self, node, *args, **kwargs):
    #     """Call a file making sure that the correct file is open."""
    #     func = kwargs.pop("_func", None)
    #     if func is None:
    #         raise RuntimeError("No function passed.")
    #     fd = self._node_io_fd
    #     if fd is None or (node._lht.filename != fd.name):
    #         if fd is not None:
    #             fd.close()
    #         self._node_io_fd = open(node._lht.filename, 'rb')
    #     kwargs["f"] = self._node_io_fd
    #     return func(node, *args, **kwargs)

    # def _node_io_loop(self, func, *args, **kwargs):
    #     """
    #     Since LHaloTrees can be split across multiple files, this
    #     optimization only works if the nodes are all in the same file.
    #     It's a small optimization that keeps the file open
    #     when doing io for multiple trees in the same file.
    #     """
    #     self._node_io_fd = None
    #     kwargs["_func"] = func
    #     super()._node_io_loop(
    #         self._func_update_file, *args, **kwargs)
    #     if self._node_io_fd is not None:
    #         self._node_io_fd.close()

    def _parse_parameter_file(self):
        """
        Parse the file header, get things like:
        - cosmological parameters
        - box size
        - list of fields
        """

        for u in ['mass', 'vel', 'len']:
            setattr(self, '_lht_units_' + u,
                    getattr(self._lht0, 'units_' + u))
            # v, s = getattr(self._lht0, 'units_' + u).split()
            # setattr(self, '_lht_units_' + u, self.quan(float(v), s))

        self.hubble_constant = self._lht0.hubble_constant
        self.omega_matter = self._lht0.omega_matter
        self.omega_lambda = self._lht0.omega_lambda
        self.box_size = self.quan(self._lht0.box_size, self._lht_units_len)
        # self.box_size = self._lht0.box_size * self._lht_units_len

        # a list of all fields on disk
        fields = self._lht0.fields
        # a dictionary of information for each field
        # this can have specialized information for reading the field
        fi = {}
        # for example:
        # fi["mass"] = {"column": 4, "units": "Msun/h", ...}
        none_keys = ['Descendant', 'FirstProgenitor', 'NextProgenitor',
                     'FirstHaloInFOFgroup', 'NextHaloInFOFgroup',
                     'Len', 'MostBoundID',
                     'SnapNum', 'FileNr', 'SubhaloIndex',
                     'uid', 'desc_uid', 'scale_factor',
                     'Jx', 'Jy', 'Jz']
        mass_keys = ['M_Mean200', 'Mvir', 'M_TopHat', 'SubHalfMass']
        dist_keys = ['x', 'y', 'z']
        velo_keys = ['VelDisp', 'Vmax', 'vx', 'vy', 'vz']
        all_keys = [none_keys, mass_keys, dist_keys, velo_keys]
        all_units = ['', self._lht_units_mass, self._lht_units_len,
                     self._lht_units_vel]
        for keylist, unit in zip(all_keys, all_units):
            try:
                self.quan(1, unit)
                punit = unit
            except UnitParseError:  # pragma: no cover
                ytreeLogger.warning(f"Could not parse unit: {unit}")
                punit = ''
            for k in keylist:
                fi[k] = {'units': punit}
            
        self.field_list = fields
        self.field_info.update(fi)

    def _plant_trees(self):
        """
        This is where we figure out how many trees there are,
        create the array to hold them, and instantiate a root
        tree_node for each tree.
        """

        if self.is_planted:
            return

        # open file, count trees
        ntrees_tot = 0
        for lht in self._lhtfiles:
            ntrees_tot += lht.ntrees
        self._size = ntrees_tot

        pbar = get_pbar("Loading tree roots", ntrees_tot)
        self._node_info['_lht'] = np.empty(ntrees_tot, dtype=object)

        itot = 0
        for ifile, lht in enumerate(self._lhtfiles):
            ntrees = lht.ntrees
            root_uids = lht.all_uids[lht.nhalos_before_tree]
            for i in range(ntrees):
                self._node_info['uid'][itot] = root_uids[i]
                self._node_info['_lht'][itot] = lht
                self._node_info['_index_in_lht'][itot] = i
                itot += 1
                pbar.update(itot)

        pbar.finish()

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        Return True if we are able to initialize a reader.
        """
        try:
            kwargs.update(silent=True, validate=True)
            LHaloTreeReader(*args, **kwargs)
        except (IOError, TypeError):
            return False
        return True
