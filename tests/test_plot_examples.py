"""
tests for the plotting examples in the docs



"""

# -----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

from ytree.testing.utilities import requires_file, TempDirTest

import ytree


def my_node(halo):
    prog = list(halo.find_root()["prog", "uid"])
    if halo["uid"] in prog:
        color = "red"
    else:
        color = "black"

    label = f"""
    id: {halo["uid"]:d}
    mass: {halo["mass"].to("Msun"):.2e} Msun
    """

    my_kwargs = {"label": label, "fontsize": 8, "shape": "square", "color": color}
    return my_kwargs


def my_edge(ancestor, descendent):
    if descendent["mass"] < ancestor["mass"]:
        color = "blue"
    elif descendent["mass"] / ancestor["mass"] > 10:
        color = "green"
    else:
        color = "black"

    my_kwargs = {"color": color, "penwidth": 5}
    return my_kwargs


AHF = "ahf_halos/snap_N64L16_000.parameter"


class TreePlotTest(TempDirTest):
    @requires_file(AHF)
    def test_tree_plot(self):
        a = ytree.load(AHF, hubble_constant=0.7)
        p = ytree.TreePlot(a[0], dot_kwargs={"rankdir": "LR", "size": '"12,4"'})
        p.save("tree.png")

    @requires_file(AHF)
    def test_tree_plot_small(self):
        a = ytree.load(AHF, hubble_constant=0.7)
        p = ytree.TreePlot(a[0], dot_kwargs={"rankdir": "LR", "size": '"12,4"'})
        p.min_mass_ratio = 0.01
        p.save("tree_small.png")

    @requires_file(AHF)
    def test_tree_plot_custom_node(self):
        a = ytree.load(AHF, hubble_constant=0.7)
        p = ytree.TreePlot(a[0], dot_kwargs={"rankdir": "BT"}, node_function=my_node)
        p.save("tree_custom_node.png")

    @requires_file(AHF)
    def test_tree_plot_custom_edge(self):
        a = ytree.load(AHF, hubble_constant=0.7)
        p = ytree.TreePlot(
            a[0],
            dot_kwargs={"rankdir": "BT"},
            node_function=my_node,
            edge_function=my_edge,
        )
        p.save("tree_custom_edge.png")
