"""
visualization imports



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np

from yt.units.yt_array import \
    YTQuantity

try:
    import pydot
except ModuleNotFoundError:
    pydot = None

class TreePlot(object):
    _min_size = 0.2
    _max_size = 2
    _min_size_field = None
    _max_size_field = None

    def __init__(self, tree, size_field='mass', size_log=True,
                 dot_kwargs=None):
        if pydot is None:
            raise RuntimeError(
                "TreePlot requires the pydot module. " +
                "You may also need to install graphviz.")

        self.tree = tree
        self.size_field = size_field
        self.size_log = size_log

        self.dot_kwargs = dict(size='"6,8"', dpi=300)
        if dot_kwargs is None:
            dot_kwargs = {}
        self.dot_kwargs.update(dot_kwargs)
        self.graph = None

    def save(self, filename=None):
        if filename is None:
            filename = 'tree_%06d.pdf' % self.tree.uid

        if self.graph is None:
            self._plot()

        suffix = filename[filename.rfind(".")+1:]
        func = getattr(self.graph, "write_%s" % suffix, None)
        if func is None:
            raise RuntimeError("Cannot save to file format: %s." % suffix)

        func(filename)
        return filename

    def _plot(self):
        self.graph = pydot.Dot(graph_type='graph', **self.dot_kwargs)
        self._plot_ancestors(self.tree)

    def _plot_ancestors(self, halo):
        graph = self.graph

        my_node = self._plot_node(halo)
        if halo.ancestors is None:
            return

        for anc in halo.ancestors:
            if self.min_mass is not None and \
              anc['mass'] < self.min_mass:
                continue
            if self.min_mass_ratio is not None and \
              anc['mass'] / anc.root['mass'] < self.min_mass_ratio:
                continue

            anc_node = self._plot_node(anc)
            graph.add_edge(pydot.Edge(my_node, anc_node, penwidth=5))
            self._plot_ancestors(anc)

    def _plot_node(self, halo):
        graph = self.graph
        node_name = "%d" % halo.uid
        my_node = graph.get_node(node_name)

        if halo.root == -1:
            halo.nodes

        if len(my_node) == 0:
            if halo in halo.root['prog']:
                color = 'red'
            else:
                color = 'black'

            my_node = pydot.Node(
                node_name, style="filled", label="",
                fillcolor=color, shape="circle",
                fixedsize="true", width=self._size_norm(halo))
            graph.add_node(my_node)
        else:
            my_node = my_node[0]

        return my_node

    def _size_norm(self, halo):
        if self._min_size_field is None:
            tdata = self.tree['tree', self.size_field]
            self._min_size_field = tdata.min()
        nmin = self._min_size_field

        if self._max_size_field is None:
            tdata = self.tree['tree', self.size_field]
            self._max_size_field = tdata.max()
        nmax = self._max_size_field

        fval = halo[self.size_field]
        if self.size_log:
            val = np.log(fval / nmin) / np.log(nmax / nmin)
        else:
            val = (fval - nmin) / (nmax - nmin)
        val = np.clip(val, 0, 1)

        size = val * (self._max_size - self._min_size) + \
          self._min_size
        return size

    _min_mass = None
    @property
    def min_mass(self):
        return self._min_mass

    @min_mass.setter
    def min_mass(self, val):
        self.graph = None
        if not isinstance(val, YTQuantity):
            val = YTQuantity(val, 'Msun')
        self._min_mass = val

    _min_mass_ratio = None
    @property
    def min_mass_ratio(self):
        return self._min_mass_ratio

    @min_mass_ratio.setter
    def min_mass_ratio(self, val):
        self.graph = None
        self._min_mass_ratio = val
