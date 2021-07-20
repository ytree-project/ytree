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

from yt.data_objects.data_containers import \
    YTDataContainer
from yt.utilities.logger import \
    ytLogger

from ytree.data_structures.arbor import \
    Arbor
from ytree.frontends.ytree.io import \
    YTreeDataFile, \
    YTreeRootFieldIO, \
    YTreeTreeFieldIO
from ytree.frontends.ytree.utilities import \
    get_about, \
    get_conditional
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
        elif nodes.dtype == object:
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
            setattr(self, attr, fh.attrs.get(attr, None))
        if "unit_registry_json" in fh.attrs:
            self.unit_registry = \
              UnitRegistry.from_json(
                  parse_h5_attr(fh, "unit_registry_json"))
        if "box_size" in fh.attrs:
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

    def get_yt_selection(self, above=None, below=None, equal=None, about=None,
                         conditionals=None, data_source=None):
        """
        Get a selection of halos meeting given criteria.

        This function can be used to create database-like queries to search
        for halos meeting various criteria. It will return a
        :class:`~yt.data_objects.selection_objects.cut_region.YTCutRegion`
        that can be queried to get field values for all halos meeting the
        selection criteria. The
        :class:`~yt.data_objects.selection_objects.cut_region.YTCutRegion`
        can then be passed to
        :func:`~ytree.frontends.ytree.arbor.YTreeArbor.get_nodes_from_selection`
        to get all the
        :class:`~ytree.data_structures.tree_node.TreeNode` objects that meet the
        criteria.

        If multiple criteria are provided, selected halos must meet all
        criteria.

        To specify a custom data container, use the ``ytds`` attribute
        associated with the arbor to access the merger tree data as a yt
        dataset. For example:

        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> ds = a.ytds

        Parameters
        ----------
        above : optional, list of tuples with (field, value, <units>)
            Halos meeting a given criterion must have field values at or
            above the provided limiting value. Each entry in the list must
            contain the field name, limiting value, and (optionally) units.
        below : optional, list of tuples with (field, value, <units>)
            Halos meeting a given criterion must have field values at or
            below the provided limiting value. Each entry in the list must
            contain the field name, limiting value, and (optionally) units.
        equal : optional, list of tuples with (field, value, <units>)
            Halos meeting a given criterion must have field values equal to
            the provided value. Each entry in the list must contain the
            field name, value, and (optionally) units.
        about : optional, list of tuples with (field, value, tolerance, <units>)
            Halos meeting a given criterion must have field values within
            the tolerance of the provided value. Each entry in the list must
            contain the field name, value, tolerance, and (optionally) units.
        conditionals : optional, list of strings
            A list of conditionals for constructing a custom
            :class:`~yt.data_objects.selection_objects.cut_region.YTCutRegion`.
            This can be used instead of above/below/equal/about to create
            more complex selection criteria. See the Cut Regions section in the
            yt documentation for more information. The conditionals keyword
            can only be used if none of the first for selection keywords are
            given.
        data_source : optional, :class:`~yt.data_objects.data_containers.YTDataContainer`
            The source yt data container to be used to make the cut region.
            If none given, the
            :class:`~yt.data_objects.static_output.Dataset.all_data` container
            (i.e., the full dataset) is used.

        Returns
        -------
        cr : :class:`~yt.data_objects.selection_objects.cut_region.YTCutRegion`
            The cut region associated with the provided selection criteria.

        Examples
        --------
        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> # select halos above 1e12 Msun at redshift > 0.5
        >>> sel = a.get_yt_selection(
        ...     above=[("mass", 1e13, "Msun"),
        ...            ("redshift", 0.5)])
        >>> print (sel["halos", "mass"])
        >>> print (sel["halos", "virial_radius"])

        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> # select halos below 1e13 Msun at redshift > 1
        >>> sel = a.get_yt_selection(
        ...     below=[("mass", 1e13, "Msun")],
        ...     above=[("redshift", 1)])
        >>> print (sel["halos", "mass"])
        >>> print (sel["halos", "virial_radius"])

        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> # select phantom halos (a consistent-trees field)
        >>> sel = a.get_yt_selection(equal=[("phantom", 1)])

        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> # select halos with vmax of 200 +-10 km/s (i.e., 5%)
        >>> sel = a.get_yt_selection(about=[("vmax", 200, "km/s", 0.05)])

        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> # use a yt conditional
        >>> sel = a.get_yt_selection(
        ...     conditionals=['obj["halos", "mass"] > 1e12'])

        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> # select halos only within a sphere
        >>> ds = a.ytds
        >>> sphere = ds.sphere(ds.domain_center, (10, Mpc))
        >>> sel = a.get_yt_selection(
        ...     above=[("mass", 1e13)],
        ...     data_source=sphere)
        >>> # get the TreeNodes for the selection
        >>> for node in a.get_nodes_from_selection(sel):
        ...     print (node["mass"])

        See Also
        --------
        select_halos, get_nodes_from_selection

        """

        if above is None:
            above = []
        if below is None:
            below = []
        if equal is None:
            equal = []
        if about is None:
            about = []
        if conditionals is None:
            conditionals = []

        if not (bool(conditionals) ^ any([above, below, equal, about])):
            raise ValueError(
                "Must specify either conditionals or above/below/equal/about, not both."
                f"\nconditionals: {conditionals}"
                f"\nabove: {above}"
                f"\nbelow: {below}"
                f"\nequal: {equal}"
                f"\nabout: {about}")

        if data_source is None:
            data_source = self.ytds.all_data()

        if not isinstance(data_source, YTDataContainer):
            raise ValueError(
                f"data_source must be a YTDataContainer: {data_source}.")

        for criterion in above:
            condition = get_conditional("above", criterion)
            conditionals.append(condition)

        for criterion in below:
            condition = get_conditional("below", criterion)
            conditionals.append(condition)

        for criterion in equal:
            condition = get_conditional("equal", criterion)
            conditionals.append(condition)

        for criterion in about:
            conditions = get_about(criterion)
            conditionals.extend(conditions)

        cr = data_source.cut_region(conditionals)
        return cr

    def get_nodes_from_selection(self, container):
        """
        Generate TreeNodes from a yt data container.

        All halos contained within the data container will be
        returned as TreeNode objects. This returns a generator
        that can be iterated over or cast as a list.

        Parameters
        ----------
        container : :class:`~yt.data_objects.data_containers.YTDataContainer`
            Data container, such as a sphere or region, from
            which nodes will be generated.

        Returns
        -------
        nodes : generator
            The :class:`~ytree.data_structures.tree_node.TreeNode` objects
            contained within the container.

        Examples
        --------
        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> c = a.arr([0.5, 0.5, 0.5], "unitary")
        >>> sphere = a.ytds.sphere(c, (0.1, "unitary"))
        >>> for node in a.get_nodes_from_selection(sphere):
        ...     print (node["mass"])

        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>> # select halos above 1e12 Msun at redshift > 0.5
        >>> sel = a.get_yt_selection(
        ...     above=[("mass", 1e13, "Msun"),
        ...            ("redshift", 0.5)])
        >>> my_nodes = list(a.get_nodes_from_selection(sel))

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

        Merger tree data is loaded as a yt dataset, providing full access
        to yt functionality. Fields are accessed with the naming convention,
        ("halos", <field name>).

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("arbor/arbor.h5")
        >>>
        >>> ds = a.ytds
        >>> sphere = ds.sphere(ds.domain_center, (5, "Mpc"))
        >>> print (sphere["halos", "mass"])
        >>>
        >>> for node in a.get_nodes_from_selection(sphere):
        ...     print (node["position"])

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
