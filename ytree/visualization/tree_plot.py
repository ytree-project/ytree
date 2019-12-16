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

from functools import wraps
import numpy as np

from yt.units.yt_array import \
    YTQuantity

try:
    import pydot
except ImportError:
    pydot = None

def clear_graph(f):
    @wraps(f)
    def newfunc(*args, **kwargs):
        rv = f(*args, **kwargs)
        args[0].graph = None
        return rv
    return newfunc

class TreePlot(object):
    """
    Make a simple merger tree plot using pydot and graphviz.

    Parameters
    ----------
    tree : merger tree node :class:`~ytree.data_structures.tree_node.TreeNode`
        The merger tree to be plotted.
    dot_kwargs : optional, dict
        A dictionary of keyword arguments to be passed to pydot.Dot.
        Default: None.

    Attributes
    ----------
    size_field : str
        The field to determine the size of each circle.
        Default: 'mass'.
    size_log : bool
        Whether to scale circle sizes based on log of size field.
        Default: True.
    min_mass : float ot YTQuantity
        The minimum halo mass to be included in the plot. If given
        as a float, units are assumed to be Msun.
        Default: None.
    min_mass_ratio : float
        The minimum ratio between a halo's mass and the mass of the
        main halo to be included in the plot.
        Default: None.

    Examples
    --------

    >>> import ytree
    >>> a = ytree.load("tree_0_0_0.dat")
    >>> p = ytree.TreePlot(a[0])
    >>> p.min_mass = 1e6 # Msun
    >>> p.save()

    """

    _min_dot_size = 0.2
    _max_dot_size = 2
    _min_field_size = None
    _max_field_size = None

    _size_field = 'mass'
    _size_log = True
    _min_mass = None
    _min_mass_ratio = None

    def __init__(self, tree, dot_kwargs=None):
        """
        Initialize a TreePlot.
        """

        if pydot is None:
            raise RuntimeError(
                "TreePlot requires the pydot module. " +
                "You may also need to install graphviz.")

        self.tree = tree

        self.dot_kwargs = dict()
        if dot_kwargs is None:
            dot_kwargs = {}
        self.dot_kwargs.update(dot_kwargs)

        self.graph = None

    def save(self, filename=None):
        """
        Save the merger tree plot.

        Parameters
        ----------
        filename: optional, str
            The output filename. If none given, the uid of the head
            node is used.
            Default: None.

        Examples
        --------

        >>> import ytree
        >>> a = ytree.load("tree_0_0_0.dat")
        >>> p = ytree.TreePlot(a[0])
        >>> p.save('tree.png')

        """

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
            halo['tree']

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
        if self._min_field_size is None:
            tdata = self.tree['tree', self.size_field]
            if self.size_log:
                self._min_field_size = tdata[tdata > 0].min()
            else:
                self._min_field_size = tdata.min()
        nmin = self._min_field_size

        if self._max_field_size is None:
            tdata = self.tree['tree', self.size_field]
            self._max_field_size = tdata.max()
        nmax = self._max_field_size

        fval = halo[self.size_field]
        if self.size_log:
            val = np.log(fval / nmin) / np.log(nmax / nmin)
        else:
            val = (fval - nmin) / (nmax - nmin)
        val = np.clip(val, 0, 1)

        size = val * (self._max_dot_size - self._min_dot_size) + \
          self._min_dot_size
        return size

    @property
    def min_mass(self):
        """
        The minimum halo mass to be included in the plot.
        """
        return self._min_mass

    @min_mass.setter
    @clear_graph
    def min_mass(self, val):
        if not isinstance(val, YTQuantity):
            val = YTQuantity(val, 'Msun')
        self._min_mass = val

    @property
    def min_mass_ratio(self):
        """
        The minimum halo mass to main halo mass.
        """
        return self._min_mass_ratio

    @min_mass_ratio.setter
    @clear_graph
    def min_mass_ratio(self, val):
        self._min_mass_ratio = val

    @property
    def size_field(self):
        """
        The field to determine the size of each circle.
        """
        return self._size_field

    @size_field.setter
    @clear_graph
    def size_field(self, val):
        self._size_field = val

    @property
    def size_log(self):
        """
        Whether to scale circle sizes based on log of size field.
        """
        return self._size_log

    @size_log.setter
    @clear_graph
    def size_log(self, val):
        self._size_log = val
