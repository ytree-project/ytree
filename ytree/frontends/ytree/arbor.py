"""
YTreeArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py
import json
import numpy as np
import os

from unyt.unit_registry import \
    UnitRegistry

from yt.utilities.logger import \
    ytLogger

from ytree.data_structures.arbor import \
    Arbor
from ytree.frontends.ytree.io import \
    YTreeDataFile, \
    YTreeRootFieldIO, \
    YTreeTreeFieldIO
from ytree.utilities.io import \
    _hdf5_yt_attr, \
    parse_h5_attr
from ytree.utilities.logger import \
    log_level
from ytree.yt_frontend import \
    YTreeDataset

class YTreeArbor(Arbor):
    """
    Class for Arbors created from the
    :func:`~ytree.data_structures.arbor.Arbor.save_arbor`
    or :func:`~ytree.data_structures.tree_node.TreeNode.save_tree` functions.
    """
    _root_field_io_class = YTreeRootFieldIO
    _tree_field_io_class = YTreeTreeFieldIO
    _suffix = ".h5"
    _node_io_attrs = ('_ai',)

    def _node_io_loop_prepare(self, nodes):
        if nodes is None:
            nodes = np.arange(self.size)
            ai = self._node_info['_ai']
        elif nodes.dtype == np.object:
            ai = np.array(
                [node._ai if node.is_root else node.root._ai
                 for node in nodes])
        else: # assume an array of indices
            ai = self._node_info['_ai'][nodes]

        # the order they will be processed
        io_order = np.argsort(ai)
        ai = ai[io_order]
        # array to return them to original order
        return_order = np.empty_like(io_order)
        return_order[io_order] = np.arange(io_order.size)

        dfi = np.digitize(ai, self._node_io._ei)
        udfi = np.unique(dfi)
        data_files = [self.data_files[i] for i in udfi]
        index_list = [io_order[dfi == i] for i in udfi]

        return data_files, index_list, return_order

    def _node_io_loop_start(self, data_file):
        data_file._field_cache = {}
        data_file.open()

    def _node_io_loop_finish(self, data_file):
        data_file._field_cache = {}
        data_file.close()

    def _parse_parameter_file(self):
        self._prefix = \
          self.filename[:self.filename.rfind(self._suffix)]

        fh = h5py.File(self.filename, mode="r")
        for attr in ["hubble_constant",
                     "omega_matter",
                     "omega_lambda"]:
            setattr(self, attr, fh.attrs[attr])
        if "unit_registry_json" in fh.attrs:
            self.unit_registry = \
              UnitRegistry.from_json(
                  parse_h5_attr(fh, "unit_registry_json"))
        self.box_size = _hdf5_yt_attr(
            fh, "box_size", unit_registry=self.unit_registry)
        self.field_info.update(
            json.loads(parse_h5_attr(fh, "field_info")))
        self._size = fh.attrs["total_trees"]
        fh.close()

        # analysis fields in sidecar files
        analysis_filename = f"{self._prefix}-analysis{self._suffix}"
        if os.path.exists(analysis_filename):
            self.analysis_filename = analysis_filename
            fh = h5py.File(analysis_filename, mode="r")
            analysis_fi = json.loads(parse_h5_attr(fh, "field_info"))
            fh.close()
            for field in analysis_fi:
                analysis_fi[field]["type"] = "analysis_saved"
            self.field_info.update(analysis_fi)
        else:
            self.analysis_filename = None

        self.field_list = list(self.field_info.keys())

    def _plant_trees(self):
        if self.is_planted:
            return

        fh = h5py.File(self.filename, "r")
        self._node_info['uid'][:] = fh["data"]["uid"][()].astype(np.int64)
        self._node_io._si = fh["index"]["tree_start_index"][()]
        self._node_io._ei = fh["index"]["tree_end_index"][()]
        fh.close()

        self._node_info['_ai'][:] = np.arange(self.size)
        self.data_files = \
          [YTreeDataFile(f"{self._prefix}_{i:04d}{self._suffix}")
           for i in range(self._node_io._si.size)]
        if self.analysis_filename is not None:
            for i, df in enumerate(self.data_files):
                df.analysis_filename = \
                  f"{self._prefix}_{i:04d}-analysis{self._suffix}"

    def get_nodes_from_yt(self, container):
        """
        Generate TreeNodes from a yt data container.

        All halos contained within the data container will be
        returned as TreeNode objects. This returns a generator
        that can be iterated over or cast as a list.

        Parameters
        ----------
        container : yt data container
            Data container, such as a sphere or region, from
            which nodes will be generated.

        Returns
        -------
        nodes : a generator of TreeNode objects

        Examples
        --------
        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> c = a.arr([0.5, 0.5, 0.5], "unitary")
        >>> sphere = a.ytds.sphere(c, (0.1, "unitary"))
        >>> for node in a.get_nodes_from_yt(sphere):
        ...     print (node)
        """

        self._plant_trees()
        container.get_data([('halos', 'file_number'),
                            ('halos', 'file_root_index'),
                            ('halos', 'tree_index')])

        file_number = container['halos', 'file_number'].d.astype(int)
        file_root_index = container['halos', 'file_root_index'].d.astype(int)
        tree_index = container['halos', 'tree_index'].d.astype(int)
        arbor_index = self._node_io._si[file_number] + file_root_index

        for ai, ti in zip(arbor_index, tree_index):
            root_node = self._generate_root_node(ai)
            if ti == 0:
                yield root_node
            else:
                yield root_node.get_node("forest", ti)

    _ytds = None
    @property
    def ytds(self):
        """
        Load as a yt dataset.
        """
        if self._ytds is not None:
            return self._ytds
        with log_level(40, mylog=ytLogger):
            self._ytds = YTreeDataset(self.filename)
        return self._ytds

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File should end in .h5, be loadable as an hdf5 file,
        and have "arbor_type" attribute.
        """
        fn = args[0]
        if not fn.endswith(self._suffix):
            return False
        try:
            with h5py.File(fn, "r") as f:
                if "arbor_type" not in f.attrs:
                    return False
                atype = f.attrs["arbor_type"]
                if hasattr(atype, "astype"):
                    atype = atype.astype(str)
                if atype != "YTreeArbor":
                    return False
        except BaseException:
            return False
        return True
