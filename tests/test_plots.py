"""
tests for plotting



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os

from ytree.utilities.testing import \
    requires_file, \
    test_data_dir, \
    TempDirTest

import ytree

CT = os.path.join(test_data_dir,
                  "consistent_trees/tree_0_0_0.dat")

class TreePlotTest(TempDirTest):
    @requires_file(CT)
    def test_default_plot(self):
        a = ytree.load(CT)
        p = ytree.TreePlot(a[0])
        p.save()

    @requires_file(CT)
    def test_non_defaults(self):
        attrs = {'size_field': 'virial_radius',
                 'size_log': False,
                 'min_mass': 1e14,
                 'min_mass_ratio': 0.1}

        a = ytree.load(CT)

        for attr, val in attrs.items():
            p = ytree.TreePlot(a[0])
            setattr(p, attr, val)
            p.save()

    @requires_file(CT)
    def test_save(self):
        a = ytree.load(CT)
        p = ytree.TreePlot(a[0])
        p.save('tree.png')

    @requires_file(CT)
    def test_dot_kwargs(self):
        a = ytree.load(CT)
        p = ytree.TreePlot(a[0], dot_kwargs={'dpi': 200})
        p.save()

    @requires_file(CT)
    def test_label_fields(self):
        a = ytree.load(CT)
        p = ytree.TreePlot(a[0], label_fields=['uid', 'mass'])
        p.save()

    @requires_file(CT)
    def test_label_fields_bad(self):
        a = ytree.load(CT)
        with self.assertRaises(RuntimeError):
            ytree.TreePlot(a[0], label_fields='notalist')

    @requires_file(CT)
    def test_node_callback(self):
        def my_func(halo):
            label = "%d" % halo['uid']
            return {"label": label}
        a = ytree.load(CT)
        p = ytree.TreePlot(a[0], node_callback=my_func)
        p.save()

    @requires_file(CT)
    def test_node_callback_bad(self):
        a = ytree.load(CT)
        with self.assertRaises(RuntimeError):
            ytree.TreePlot(a[0], node_callback='notafunc')
